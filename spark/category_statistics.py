from pyspark.sql import SparkSession
from pyspark.sql.functions import desc, asc, col, sum
import os, json

PRODUCTION = True if ("PRODUCTION" in os.environ) else False
DATABASE_IP = os.environ["DB_URL"] if ("DB_URL" in os.environ) else "localhost"

builder = SparkSession.builder.appName("category_statistics")

if (not PRODUCTION):
    builder = builder.master("local[*]")

spark = builder.config("spark.driver.extraClassPath", "mysql-connector-j-8.0.33.jar").getOrCreate()
spark.sparkContext.setLogLevel(logLevel="ERROR")

df_category = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/Shop") \
    .option("dbtable", "Shop.category") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

df_product_category = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/Shop") \
    .option("dbtable", "Shop.productcategory") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

df_order_product = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/Shop") \
    .option("dbtable", "Shop.orderproduct") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

df_order = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/Shop") \
    .option("dbtable", "Shop.order") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

df_complete = df_product_category.alias("pc") \
    .join(df_order_product.alias("op"), col("op.productId") == col("pc.productId")) \
    .join(df_order.alias("o"), col("op.orderId") == col("o.id"))\
    .where(col("o.status") == "COMPLETE")

#ALIAS com izostavljen
df_join = df_category.alias("c") \
    .join(df_complete.alias("com"), col("com.categoryId") == col("c.id"), "left")

df_count = df_join.groupBy("c.name").agg(sum("com.quantity").alias("count"))
df_sorted = df_count.orderBy(desc("count"), asc("c.name"))

df_result = df_sorted.select("c.name").withColumnRenamed("c.name", "statistics")


result_list = df_result.toJSON().collect()
print(result_list)
category_names = [json.loads(json_str)["name"] for json_str in result_list]
result_dict = {"statistics": category_names}

result_json_str = json.dumps(result_dict)
print(result_dict)
with open("/app/category_statistics.json", "w") as f:
    f.write(result_json_str)

spark.stop()


