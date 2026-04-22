from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField,
    LongType, TimestampType, StringType, ArrayType
)
from pyspark.sql import functions as F

# Read raw TSV — event_list and product_list ingested as StringType first
raw_schema = StructType([
    StructField("hit_time_gmt",  LongType(),      False),
    StructField("date_time",      TimestampType(), False),
    StructField("user_agent",     StringType(),    True),
    StructField("ip",             StringType(),    True),
    StructField("event_list",     StringType(),    True),
    StructField("geo_city",       StringType(),    True),
    StructField("geo_region",     StringType(),    True),
    StructField("geo_country",    StringType(),    True),
    StructField("pagename",       StringType(),    True),
    StructField("page_url",       StringType(),    True),
    StructField("product_list",   StringType(),    True),
    StructField("referrer",       StringType(),    True),
])

df = (
    spark.read.csv(
        "./data.sql",
        schema=raw_schema,
        sep="\t",
        header=True,
        timestampFormat="yyyy-MM-dd HH:mm:ss",
    )
    # event_list: comma-separated event codes → Array[String]
    .withColumn(
        "event_list",
        F.when(F.col("event_list").isNotNull(),
               F.split(F.col("event_list"), ","))
         .otherwise(F.lit(None))
    )
    # product_list: semicolon-separated product entries → Array[String]
    .withColumn(
        "product_list",
        F.when(F.col("product_list").isNotNull(),
               F.split(F.col("product_list"), ";"))
         .otherwise(F.lit(None))
    )
)