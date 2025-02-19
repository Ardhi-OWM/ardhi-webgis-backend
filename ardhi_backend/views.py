from rest_framework.permissions import AllowAny
from rest_framework import viewsets, status
from rest_framework.response import Response
from django.http import JsonResponse
from django.conf import settings
import requests
import boto3
import json
import csv
import xml.etree.ElementTree as ET
from io import StringIO
from urllib.parse import urlparse
from rest_framework.exceptions import ValidationError
from .models import Input, Subscription, APIEndpoint
from .serializers import InputSerializer, SubscriptionSerializer, APIEndpointSerializer
from fastkml import kml  
import geopandas as gpd  
from rest_framework.decorators import action


# -----------------------------------
# ✅ Generate Signed URL for Cloud Storage Access
# -----------------------------------
def get_s3_signed_url(bucket_name, file_key):
    """
    Generate a presigned URL for frontend access to a file stored in S3-compatible storage.
    """
    s3 = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )
    try:
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": file_key},
            ExpiresIn=3600  # URL expires in 1 hour
        )
        return presigned_url
    except Exception as e:
        return str(e)

# -----------------------------------
# ✅ Handle Model Upload, Validation, and Processing
# -----------------------------------
class InputViewSet(viewsets.ModelViewSet):
    serializer_class = InputSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return Input.objects.filter(user_id=user_id)
        return Input.objects.all()

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        input_type = self.request.data.get("input_type")
        data_link = self.request.data.get("data_link")

        if not user_id or not data_link:
            return Response({"error": "user_id and data_link are required"}, status=400)

        print(f"🔹 Received input: {input_type} - {data_link}")

        if input_type == "Model":
            cloud_provider = self.get_cloud_provider(data_link)
            file_type = self.get_file_type(data_link)

            print(f"✅ Detected Cloud Provider: {cloud_provider}")  
            print(f"✅ Detected File Type: {file_type}")

            if not file_type:
                print("❌ Error: File type detection failed!")
                return Response({"error": "Could not detect file type from URL."}, status=400)

            processed_data = None
            signed_url = None

            try:
                print(f"🔹 Fetching file from {data_link} ...")
                response = requests.get(data_link, timeout=10)
                response.raise_for_status()
                file_content = response.text  

                print(f"✅ Successfully fetched file content!")

                if file_type in ["json", "geojson"]:
                    try:
                        processed_data = response.json()
                        print(f"✅ Processed JSON: {processed_data}")
                    except json.JSONDecodeError as json_err:
                        print(f"❌ JSON Parsing Error: {json_err}")
                        return Response({"error": f"Invalid JSON format: {str(json_err)}"}, status=400)
                elif file_type == "csv":
                    processed_data = self.convert_csv_to_geojson(file_content)
                elif file_type in ["xml", "kml", "gpx"]:
                    processed_data = self.convert_xml_to_geojson(file_content)
                elif file_type in ["tif", "tiff"]:
                    signed_url = get_s3_signed_url(settings.S3_BUCKET_NAME, data_link.split("/")[-1])
                else:
                    print(f"❌ Unsupported File Type: {file_type}")
                    return Response({"error": f"Unsupported file type: {file_type}"}, status=400)

                print(f"✅ Model Processing Successful! Processed Data: {processed_data}")

            except requests.exceptions.RequestException as req_err:
                print(f"❌ Network Error: {req_err}")
                return Response({"error": f"Network error while fetching model: {str(req_err)}"}, status=500)
            except Exception as e:
                print(f"❌ Unexpected Error: {str(e)}")
                return Response({"error": f"Internal Server Error: {str(e)}"}, status=500)

            # ✅ Save Processed Model Data
            serializer.save(
                user_id=user_id,
                input_type=input_type,
                data_link=data_link,
                cloud_provider=cloud_provider,
                file_type=file_type.upper() if file_type else None,
                processed_data=json.dumps(processed_data) if processed_data else None,
                signed_url=signed_url
            )

            print(f"✅ Successfully saved model for user {user_id}")

            return Response(serializer.data, status=201)

        else:
            serializer.save(user_id=user_id, input_type=input_type, data_link=data_link)
            return Response(serializer.data, status=201)

    def get_cloud_provider(self, url):
        """ Detects which cloud provider the link belongs to """
        if "amazonaws.com" in url:
            return "AWS"
        elif "storage.googleapis.com" in url:  # ✅ Fix for Google Cloud Storage
            return "Google Cloud"
        elif "digitaloceanspaces.com" in url:
            return "DigitalOcean"
        elif "dropbox.com" in url:
            return "Dropbox"
        else:
            return "Unknown"

    def get_file_type(self, url):
        """ Extracts file type from the URL """
        parsed_url = urlparse(url)
        path = parsed_url.path
        file_extension = path.split(".")[-1].lower()

        print(f"🔹 Extracted File Extension: {file_extension}")

        if file_extension in ["json", "geojson", "csv", "xml", "kml", "gpx", "tif", "tiff"]:
            return file_extension
        else:
            print("❌ Unsupported file extension detected!")
            return None

    def convert_csv_to_geojson(self, csv_text):
        """
        Convert CSV data into GeoJSON format.
        The CSV must have 'latitude' and 'longitude' columns.
        """
        try:
            csv_reader = csv.DictReader(StringIO(csv_text))
            features = []

            for row in csv_reader:
                if "latitude" in row and "longitude" in row:
                    features.append({
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [float(row["longitude"]), float(row["latitude"])]
                        },
                        "properties": {k: v for k, v in row.items() if k not in ["latitude", "longitude"]}
                    })

            return {"type": "FeatureCollection", "features": features}
        except Exception as e:
            return {"error": f"Failed to convert CSV: {str(e)}"}

    def convert_xml_to_geojson(self, xml_text):
        """
        Convert XML/KML/GPX into GeoJSON format, supporting Point, Polygon, and MultiPolygon.
        """
        try:
            root = ET.fromstring(xml_text)
            geojson_data = {"type": "FeatureCollection", "features": []}

            for placemark in root.findall(".//{http://www.opengis.net/kml/2.2}Placemark"):
                coordinates = placemark.find(".//{http://www.opengis.net/kml/2.2}coordinates")
                if coordinates is not None:
                    coords = coordinates.text.strip().split(" ")
                    parsed_coords = [list(map(float, coord.split(",")))[:2] for coord in coords]

                    if len(parsed_coords) == 1:
                        geometry_type = "Point"
                        geometry_data = {"type": geometry_type, "coordinates": parsed_coords[0]}
                    elif parsed_coords[0] == parsed_coords[-1]:
                        geometry_type = "Polygon"
                        geometry_data = {"type": geometry_type, "coordinates": [parsed_coords]}
                    else:
                        geometry_type = "MultiPolygon"
                        geometry_data = {"type": geometry_type, "coordinates": [[parsed_coords]]}
                    
                    geojson_data["features"].append({
                        "type": "Feature",
                        "geometry": geometry_data,
                        "properties": {"name": placemark.findtext(".//{http://www.opengis.net/kml/2.2}name", "")}
                    })
            return geojson_data
        except Exception as e:
            return {"error": f"Failed to convert XML/KML/GPX: {str(e)}"}


# -----------------------------------
# ✅ API Endpoint Management
# -----------------------------------
class APIEndpointViewSet(viewsets.ModelViewSet):
    serializer_class = APIEndpointSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return APIEndpoint.objects.filter(user_id=user_id)
        return APIEndpoint.objects.all()

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        api_url = self.request.data.get("api_url")

        if not user_id:
            raise ValidationError({"error": "user_id is required"})

        if APIEndpoint.objects.filter(api_url=api_url, user_id=user_id).exists():
            raise ValidationError({"detail": "This API URL already exists for this user."})

        serializer.save(user_id=user_id)

    @action(detail=False, methods=['delete'])
    def delete_by_api_url(self, request):
        api_url = request.data.get("api_url")
        if not api_url:
            return Response({"error": "api_url is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = APIEndpoint.objects.get(api_url=api_url)
            instance.delete()
            return Response({"message": "API Endpoint deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except APIEndpoint.DoesNotExist:
            return Response({"error": "API Endpoint not found"}, status=status.HTTP_404_NOT_FOUND)


# -----------------------------------
# ✅ Subscription Management
# -----------------------------------
class SubscriptionViewSet(viewsets.ModelViewSet):
    serializer_class = SubscriptionSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        user_id = self.request.query_params.get("user_id")
        if user_id:
            return Subscription.objects.filter(user_id=user_id)
        return Subscription.objects.all()

    def perform_create(self, serializer):
        user_id = self.request.data.get("user_id")
        email = self.request.data.get("email")

        if not user_id:
            raise ValidationError({"error": "user_id is required"})

        if Subscription.objects.filter(email=email).exists():
            raise ValidationError({"error": "This email is already subscribed."})

        serializer.save(user_id=user_id)


# -----------------------------------
# ✅ Home API Endpoint
# -----------------------------------
def home(request):
    return JsonResponse({"message": "Welcome to Ardhi WebGIS API"})
