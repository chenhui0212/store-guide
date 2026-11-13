#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
基础设施连接冒烟测试
"""
import os

import pytest
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def test_milvus():
    """测试 Milvus 连接"""
    from pymilvus import MilvusClient

    client = MilvusClient(uri=os.getenv("MILVUS_URI"))
    try:
        version = client.get_server_version()
        assert version, "Milvus 未返回版本号"
    finally:
        client.close()


def test_neo4j():
    """测试 Neo4j 连接"""
    from neo4j import GraphDatabase

    uri = os.getenv("NEO4J_URI")
    auth = (
        os.getenv("NEO4J_USERNAME"),
        os.getenv("NEO4J_PASSWORD"),
    )
    with GraphDatabase.driver(uri, auth=auth) as driver:
        driver.verify_connectivity()
        with driver.session() as session:
            record = session.run("RETURN 1 AS num").single()
    assert record and record["num"] == 1


def test_postgres():
    """测试 PostgreSQL 连接"""
    from psycopg import connect

    uri = os.getenv("POSTGRES_URI")
    with connect(uri) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            assert cur.fetchone() == (1,)


def test_minio():
    """测试 MinIO 连接"""
    from minio import Minio

    client = Minio(
        os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESS_KEY"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False,
    )
    buckets = client.list_buckets()
    assert isinstance(buckets, list), "MinIO 未返回存储桶列表"


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-v"]))
