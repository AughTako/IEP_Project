from flask import Flask, jsonify, json
import os
import subprocess

application = Flask(__name__)


@application.route("/product_statistics", methods=["GET"])
def product_statistics():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/product_statistics.py"
    os.environ["SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"

    result = subprocess.run(["/template.sh"])

    result_list = []

    if os.path.exists("/app/product_statistics.json"):
        with open("/app/product_statistics.json", "r+") as f:
            for line in f:
                json_object = json.loads(line)
                result_list.append(json_object)

        os.remove("/app/product_statistics.json")

    response = {
        "statistics": result_list
    }

    return jsonify(response), 200


@application.route("/category_statistics", methods=["GET"])
def category_statistics():
    os.environ["SPARK_APPLICATION_PYTHON_LOCATION"] = "/app/category_statistics.py"
    os.environ["SPARK_SUBMIT_ARGS"] = "--driver-class-path /app/mysql-connector-j-8.0.33.jar --jars /app/mysql-connector-j-8.0.33.jar"

    result = subprocess.run(["/template.sh"])

    response = []

    if os.path.exists("/app/category_statistics.json"):
        with open("/app/category_statistics.json", "r+") as f:
            for line in f:
                json_object = json.loads(line)
                response = json_object

        os.remove("/app/category_statistics.json")
    else:
        response = {
            "statistics": []
        }

    return jsonify(response), 200


if __name__ == "__main__":
    application.run(debug=True, host="0.0.0.0", port=5005)
