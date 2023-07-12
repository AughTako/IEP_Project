from pyspark.sql import SparkSession
import os
from pyspark.sql.functions import col, sum

PRODUCTION = True if ("PRODUCTION" in os.environ) else False
DATABASE_IP = os.environ["DB_URL"] if ("DB_URL" in os.environ) else "localhost"

builder = SparkSession.builder.appName("product_statistics")

if (not PRODUCTION):
    builder = builder.master("local[*]")

spark = builder.config("spark.driver.extraClassPath", "mysql-connector-j-8.0.33.jar").getOrCreate()
spark.sparkContext.setLogLevel(logLevel="ERROR")

product_df = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/Shop") \
    .option("dbtable", "Shop.product") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

orderproduct_df = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/Shop") \
    .option("dbtable", "Shop.orderproduct") \
    .option("user", "root") \
    .option("password", "root") \
    .load()

order_df = spark.read \
    .format("jdbc") \
    .option("driver", "com.mysql.cj.jdbc.Driver") \
    .option("url", f"jdbc:mysql://{DATABASE_IP}:3306/Shop") \
    .option("dbtable", "Shop.order") \
    .option("user", "root") \
    .option("password", "root") \
    .load()


join_df = product_df.alias("pr") \
    .join(orderproduct_df.alias("op"), col("op.productId") == col("pr.id")) \
    .join(order_df.alias("o"), col("o.id") == col("op.orderId"))

sold_df = join_df.where(col("o.status") == "COMPLETE") \
    .groupBy("pr.name") \
    .agg(sum("op.quantity").alias("sold"))\
    .select(col("pr.name").alias("name"), col("sold"))

waiting_df = join_df.filter(col("o.status") != "COMPLETE") \
    .groupBy("pr.name") \
    .agg(sum("op.quantity").alias("waiting"))\
    .select(col("pr.name").alias("name"), col("waiting"))

result_df = product_df.alias("pr")\
    .join(sold_df.alias("s"), col("s.name") == col("pr.name"), "left") \
    .join(waiting_df.alias("w"), col("w.name") == col("pr.name"), "left") \
    .na.fill(0)\
    .where(col("sold") + col("waiting") > 0)\
    .select(col("pr.name").alias("name"), col("sold"), col("waiting"))

# result_df = sold_df.alias("s") \
#     .join(waiting_df.alias("w"), col("s.name") == col("w.name")) \
#     .select(col("s.name").alias("name"), col("s.sold").alias("sold"), col("w.waiting").alias("waiting")) \
#     .na.fill(0)

result_list = result_df.toJSON().collect()
print(result_list)

with open("/app/product_statistics.json", "w") as f:
    for json_str in result_list:
        f.write(json_str + "\n")


spark.stop()





#sold_df = product_df.alias("pr") \
#     .join(orderproduct_df.alias("op"), col("op.productId") == col("pr.id")) \
#     .join(order_df.alias("o"), col("o.id") == col("op.orderId")) \
#     .where(col("o.status") == "COMPLETE") \
#     .groupBy("pr.name") \
#     .agg(sum("op.quantity").alias("sold"))
#
# sold_products_ids = orderproduct_df.alias("op")\
#                     .join(order_df.alias("o"), col("o.id") == col("op.orderId"))\
#                     .where(col("o.status") == "COMPLETE")\
#                     .select("op.productId")\
#                     .distinct().rdd.flatMap(lambda x: x).collect()
# print(sold_products_ids)
#
# waiting_df = product_df.alias("pr") \
#     .join(orderproduct_df.alias("op"), col("op.productId") == col("pr.id")) \
#     .join(order_df.alias("o"), col("o.id") == col("op.orderId")) \
#     .where((col("o.status") != "COMPLETE") & (col("pr.id").isin(sold_products_ids))) \
#     .groupBy("pr.name") \
#     .agg(sum("op.quantity").alias("waiting"))
#
# result_df = product_df.alias("p") \
#     .join(sold_df.alias("s"), col("s.name") == col("p.name"), "right") \
#     .join(waiting_df.alias("w"), col("w.name") == col("p.name"), "left") \
#     .select("p.name", col("s.sold").alias("sold"), col("w.waiting").alias("waiting")) \
#     .na.fill(0)



# sold_df = product_df.alias("pr") \
#     .join(orderproduct_df.alias("op"), col("op.productId") == col("pr.id")) \
#     .join(order_df.alias("o"), col("o.id") == col("op.orderId")) \
#     .where(col("o.status") == "COMPLETE") \
#     .groupBy("pr.name") \
#     .agg(sum("op.quantity").alias("sold"))
#
# sold_products_ids = orderproduct_df.join(order_df, order_df["id"] == orderproduct_df["orderId"]).filter(col("status") == "COMPLETE")\
#                               .select("productId").distinct().rdd.flatMap(lambda sold_products_ids: sold_products_ids).collect()
# print(sold_products_ids)
#
# waiting_df = product_df.alias("pr") \
#     .join(orderproduct_df.alias("op"), col("op.productId") == col("pr.id")) \
#     .join(order_df.alias("o"), col("o.id") == col("op.orderId")) \
#     .where((col("o.status") != "COMPLETE") &
#            (col("pr.id").isin(orderproduct_df.join(order_df, order_df["id"] == orderproduct_df["orderId"]).filter(col("status") == "COMPLETE")
#                               .select("productId").distinct().rdd.flatMap(lambda sold_products_ids: sold_products_ids).collect()))) \
#     .groupBy("pr.name") \
#     .agg(sum("op.quantity").alias("waiting"))
#
# result_df = product_df.alias("p") \
#     .join(sold_df.alias("s"), col("s.name") == col("p.name"), "right") \
#     .join(waiting_df.alias("w"), col("w.name") == col("p.name"), "left") \
#     .select("p.name", col("s.sold").alias("sold"), col("w.waiting").alias("waiting")) \
#     .na.fill(0)