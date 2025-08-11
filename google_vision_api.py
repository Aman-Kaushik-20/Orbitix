from google.cloud import vision
import os
import json
from backend.src.utils.constants import GCP_CREDENTIALS

# Set the GOOGLE_APPLICATION_CREDENTIALS environment variable
# Replace 'path/to/your/key.json' with the actual path to your service account key file
# This is crucial for authentication if you are not running in a Google Cloud environment
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = json.dumps({
  "type": "service_account",
  "project_id": "aman-project-468014",
  "private_key_id": "90437599acb42b42dce7607349cdbbf4f572f52d",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQChIibWNh7C8I81\nZd2BlobitbyBhH+YKc0d/4u8ETvf/3C5Mr8JIYJNgHr+MC6UKKKVG8llyJ3P9HLJ\nygnXZJCfuGLxRJC+0pCWSvzyXCjLWysvroijB6qQYNlHcFiYOKfl/4dU1ZSdJeKp\nAqMzgThcc8GfoxuFIbAjwojV4RpDqXzOqMM9GvWUkLHwLJultGDkqx3L4tOuc9v4\n7WaNWHmKiOlTo7jWwJQfjp3eAPw2bA8HkkJqJmTcXRyfoOwHIb0zPe9EBrL9eR6N\nJ9JptIw33hBHrdSmdpIr+R0/aW3hHxpVV9faW1mVBWLcfvom4raDXMMNXzx2uXVv\nnSkhXQLTAgMBAAECggEAC1zaq0FuwuVu29+ekqxYP7V8IRAEZWkRN1vVcUIv3Dhp\nrQ2ojg7IXwm/4pvoNPd2m5g1iBFxG4CL9bHjJsbHMhQxGf1xTZuQqaCJHNgl4k1A\nCuE+bmy0ePDzcYe5H6bjJCN0WiWjkL9ir/NpKdEjddWN4mGAp8872hG2T4rLrNiy\nrwjMxSs9LsLFtYEWK/a6vaTodbCZANoHgE6eVCtxjrQcdTJktRchSmZOVUFk5v0q\nOwr2oEYYRe+Kx9SFKIGSWiotiI2w1pSGnK8vBE4SakPAfcahbHIB4bteHCdehpTz\nrwvW8bPmnXAhG7a/ppRImf6GhsLtEsuHP2JKH8GfTQKBgQDV4fy+MpBX89C/gF6p\nFcxPvxA+a/CoKFYLw66ruStYVB6ZQQSsOD8zK+hI7AR68bsyGdLkohzbA6tejFxF\n0fd7yBfN5QIT7KOO9lgrtt7xP10d/itkVse4AXHehND/5OuC7N5LCjPm67MlSxTH\n1c3sc4sKa8eHNMQqkpYYKkMvvQKBgQDA3QY19IWqj/DACo6RXzGQASXgT6Eli1JV\nk4uixa0FLOfvj4N/FxsEv33aqUUk/VcyY5YBgsF4HnHVmMboPCjZ0e3zWq9ZcviP\nDR1ibU+Yyq8obrogJyqqbntmTmLFdC9BjHORb6PQ3dkl85Ri0rSBezEppTIgPM0L\n/zQEeLUdzwKBgQDQPyLZBV5pZGmBq7l/JEwz8TIdtPcyo2N0POkbJkW/0NeiHB4y\nmOlgJ4YZSkPqeObtFxuxpO43iNEYU82b5Z3zlZUn0aw+Pg/aKJ0cowdbGXjOtSUG\noz/+Ntnp8KOWJAvzBDJEGgEC+8cHrpzjHZdMfAuK7/nr+UJuuR8PFEcqeQKBgQC5\nqw5zmvejf/cRqhgeMzqPm8tO6toEPuAAqo5fIVa0CMswgUTicOf95ivO+e4q8gmj\n5ONgiPSgIw8LxoyWvnPFXqhpAwCUaG6JqOKFAx8BxP5jOlXM5mfYs4vwrb3AwV1N\nCV2owYU/apPGSXystpQ3otVtdi+PgXkU95aoR1x1WQKBgBeeaftAjoYeqiRYereG\nL5iajT+8yTGAu2Zc92w2700DbBJA4kEMsHsx4lF4zDn6FdyiCdNIsT8jBOqv6TKD\nYnSIP+IXfO0CHaY6mJdkTI0EzpgMvquqLk2DTXCO/LIygs9m0aSyGBEEpfC14O5J\nwMSdjAw5v2M56WcUzpvzZk0b\n-----END PRIVATE KEY-----\n",
  "client_email": "travel-agent-testing@aman-project-468014.iam.gserviceaccount.com",
  "client_id": "115905133353144020301",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/travel-agent-testing%40aman-project-468014.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
)

def detect_labels_uri(uri):
    """Detects labels in the image located in Google Cloud Storage or on the
    Web."""
    client = vision.ImageAnnotatorClient()
    image = vision.Image()
    image.source.image_uri = uri

    response = client.label_detection(image=image)
    labels = response.label_annotations
    print("Labels:")

    for label in labels:
        print(f'"{label.description}"')

    if response.error.message:
        raise Exception(
            f"{response.error.message}\nFor more info on error messages, check: "
            "https://cloud.google.com/apis/design/errors"
        )

# Example usage: Replace with your image URI
detect_labels_uri("https://storage.googleapis.com/travel_x/untitled-design-374.jpg")
