#!/usr/bin/env python
# coding: utf-8

from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, IntegerType, BooleanType,
    LongType, TimestampType, StringType, ArrayType
)
from pyspark.sql.functions import udf, lit, desc
from urllib.parse import urlparse, parse_qs, unquote
from pyspark.sql.functions import col, when, split, sum as spark_sum
from datetime import datetime
from enum import IntEnum
import re


from enum import IntEnum

class Status(IntEnum):
    """User interaction and transaction status codes."""
    PURCHASE = 1
    PRODUCT_VIEW = 2
    SHOPPING_CART_OPEN = 10
    SHOPPING_CART_CHECKOUT = 11
    SHOPPING_CART_ADD = 12
    SHOPPING_CART_REMOVE = 13
    SHOPPING_CART_VIEW = 14

    @classmethod
    def from_value(cls, value: int):
        """Helper to convert an integer back to the Enum member."""
        try:
            return cls(value)
        except ValueError:
            return None

class TrafficAnalysis:
    """ Traffic Analysis Helper Class"""

    def extract_domain(self, url: str):
        """ Extract Domain name from URL"""
        if url is None:
            return None
        
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            # Remove 'www.' prefix if present
            domain = re.sub(r'^www\.', '', domain)
            return domain if domain else None
        except Exception as e:
            print(f"Error extract_domain method: {e}")
            return None

    def get_rev(self, product_list):
        """ Calculate the Total Revenue from product attributes"""

        total = 0

        if not product_list:
            return total

        try:
            # check if product_list is type list
            if isinstance(product_list, list) and len(product_list) > 0:
                # Iterate through product_list
                for product in product_list:
                    # Get Total revenue is index 3
                    p = product.split(";")[3]          
                    # Check the value and evaluate to zero if not
                    p_rev = 0 if not p else int(p)
                    # print(f"p_rev: {p_rev}")
                    total = total + p_rev
            else:
                # Total revenue is index 3
                p = product.split(";")[3]             
                total = 0 if not p else int(p) 
        except Exception as e:
            print(f"Error get_rev function: {e}")

        # print(f"total: {total}")
        return total

    def is_purchase_order(self, event_list: list[int], purchase_event: int):
        """ Filter purchase orders by status"""
        if not event_list:
            return False

        return True if purchase_event in event_list else False

    def extract_keywords(self, url: str):
        """ Extract URL query keywords from URL using keyword keys"""
        try:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            keywords_list = []

            # Define common keys that indicate search keywords
            keyword_keys = {'q', 'p'}

            for key, values in query_params.items():
                if key.lower() in keyword_keys:
                    for value in values:
                        decoded_value = unquote(value)
                        clean_value = decoded_value.strip()
                        if clean_value:
                            keywords_list.append(clean_value)

            final_keywords = ", ".join(keywords_list)
        except Exception as e:
            print(f"Error extract_keywords func")
            return None

        return final_keywords





def main():

    spark = SparkSession.builder \
        .appName("traffic-analysis") \
        .master("local[*]") \
        .getOrCreate()



    # Read raw TSV — event_list and product_list ingested as StringType first
    raw_schema = StructType([
        StructField("hit_time_gmt",   LongType(),      False),
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
            "./data/data.sql",
            schema=raw_schema,
            sep="\t",
            header=True,
            timestampFormat="yyyy-MM-dd HH:mm:ss",
        )
        # event_list: comma-separated event codes → Array[Integer]
        .withColumn(
            "event_list",
            when(col("event_list").isNotNull(),
                split(col("event_list"), ",").cast(ArrayType(IntegerType())))
            .otherwise(lit(None))
        )
        # product_list: comma-separated product entries → Array[String]
        .withColumn(
            "product_list",
            when(col("product_list").isNotNull(),
                split(col("product_list"), ","))
            .otherwise(lit(None))
        )
    )

    traffic_analyzer = TrafficAnalysis()

    # Register UDF Functions
    is_purchase_order_udf = udf(traffic_analyzer.is_purchase_order, BooleanType())
    get_rev_udf = udf(traffic_analyzer.get_rev, IntegerType())
    extract_domain_udf = udf(traffic_analyzer.extract_domain, StringType())
    extract_keywords_udf = udf(traffic_analyzer.extract_keywords, StringType())



    # add two columns domain and revenue to the dataframe
    df = df.withColumn("domain", extract_domain_udf("referrer")).withColumn("revenue", get_rev_udf("product_list"))


    # Get the purchased traffic
    purchased_traffic_df = (
        df
        .select("ip", "revenue")
        .filter(is_purchase_order_udf(col("event_list"), lit(Status.PURCHASE)))
        .groupBy("ip")
        .agg(spark_sum("revenue").alias("total_revenue"))
    )

    
    # Get only searchengine web traffic
    visit_traffic_df = df.select("ip", "domain", "referrer").filter((col("domain") != "esshopzilla.com")).withColumn('keywords', extract_keywords_udf("referrer"))


    # Join the traffic with ip
    joined_df = purchased_traffic_df.join(visit_traffic_df, on="ip", how="left")

    # Output the traffic
    output_df = joined_df.select("domain", "keywords", "total_revenue").sort(desc("total_revenue"))
    output_df.show()



    today = datetime.now()
    output_filename = f"{today.strftime('%Y-%m-%d')}_SearchKeywordPerformance.tab"


    output_df.coalesce(1).write.mode("overwrite").option("header", "true").option("sep", "\t").csv(f"./output/{output_filename}")



if __name__ == "__main__":
    main()