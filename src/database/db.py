"""Gerenciamento de banco de dados SQLite em memória para os dados da Empório da Música.

Carrega e normaliza os dados de todos os CSVs operacionais (produtos, categorias,
clientes, pedidos, itens e promoções), oferecendo consultas relacionais otimizadas.
"""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from src.config import settings


class DatabaseManager:
    """Singleton gerenciador do banco de dados relacional SQLite em memória."""

    _instance: Optional[DatabaseManager] = None
    _connection: Optional[sqlite3.Connection] = None

    def __new__(cls) -> DatabaseManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_connection(self) -> sqlite3.Connection:
        if self._connection is None:
            self._connection = sqlite3.connect(":memory:", check_same_thread=False)
            self._connection.row_factory = sqlite3.Row
            self._init_schema_and_data(self._connection)
        return self._connection

    def _init_schema_and_data(self, conn: sqlite3.Connection) -> None:
        """Cria as tabelas relacionais com tipagem apropriada e carrega os dados dos CSVs."""
        cursor = conn.cursor()

        # 1. Esquemas das Tabelas
        cursor.executescript("""
            CREATE TABLE categories (
                category_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT
            );

            CREATE TABLE customers (
                customer_id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT NOT NULL,
                city TEXT NOT NULL
            );

            CREATE TABLE products (
                product_id INTEGER PRIMARY KEY,
                price_brl REAL NOT NULL,
                name TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                description TEXT,
                stock_quantity INTEGER NOT NULL DEFAULT 0,
                status TEXT NOT NULL,
                specs TEXT,
                created_at TEXT,
                FOREIGN KEY (category_id) REFERENCES categories (category_id)
            );

            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                order_date TEXT NOT NULL,
                status TEXT NOT NULL,
                total_brl REAL NOT NULL,
                payment_method TEXT,
                tracking_code TEXT,
                estimated_delivery TEXT,
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
            );

            CREATE TABLE order_items (
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL DEFAULT 1,
                FOREIGN KEY (order_id) REFERENCES orders (order_id),
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );

            CREATE TABLE promotions (
                promotion_id INTEGER PRIMARY KEY,
                product_id INTEGER NOT NULL,
                discount_percent REAL NOT NULL,
                description TEXT,
                is_active INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (product_id) REFERENCES products (product_id)
            );

            CREATE INDEX idx_products_cat ON products(category_id);
            CREATE INDEX idx_orders_cust ON orders(customer_id);
            CREATE INDEX idx_order_items_order ON order_items(order_id);
            CREATE INDEX idx_order_items_prod ON order_items(product_id);
            CREATE INDEX idx_promos_prod ON promotions(product_id);
        """)

        # 2. Carga dos dados CSVs
        data_dir = settings.DATA_DIR
        self._load_csv_to_table(conn, data_dir / "desafio_tecnico_ai_eng - categories.csv", "categories", [
            ("category_id", int),
            ("name", str),
            ("description", str),
        ])

        self._load_csv_to_table(conn, data_dir / "desafio_tecnico_ai_eng - customers.csv", "customers", [
            ("customer_id", int),
            ("name", str),
            ("phone", str),
            ("email", str),
            ("city", str),
        ])

        self._load_csv_to_table(conn, data_dir / "desafio_tecnico_ai_eng - products.csv", "products", [
            ("product_id", int),
            ("price_brl", float),
            ("name", str),
            ("category_id", int),
            ("description", str),
            ("stock_quantity", int),
            ("status", str),
            ("specs", str),
            ("created_at", str),
        ])

        self._load_csv_to_table(conn, data_dir / "desafio_tecnico_ai_eng - orders.csv", "orders", [
            ("order_id", int),
            ("customer_id", int),
            ("order_date", str),
            ("status", str),
            ("total_brl", float),
            ("payment_method", str),
            ("tracking_code", str),
            ("estimated_delivery", str),
            ("notes", str),
        ])

        self._load_csv_to_table(conn, data_dir / "desafio_tecnico_ai_eng - order_items.csv", "order_items", [
            ("order_id", int),
            ("product_id", int),
            ("quantity", int),
        ])

        self._load_csv_to_table(conn, data_dir / "desafio_tecnico_ai_eng - promotions.csv", "promotions", [
            ("promotion_id", int),
            ("product_id", int),
            ("discount_percent", float),
            ("description", str),
            ("is_active", int),
        ])

        conn.commit()

    def _load_csv_to_table(
        self,
        conn: sqlite3.Connection,
        csv_path: Path,
        table_name: str,
        columns: list[tuple[str, type]],
    ) -> None:
        if not csv_path.exists():
            return

        with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            col_names = [c[0] for c in columns]
            placeholders = ", ".join(["?"] * len(col_names))
            sql = f"INSERT INTO {table_name} ({', '.join(col_names)}) VALUES ({placeholders})"

            rows_to_insert = []
            for row in reader:
                values = []
                for col_name, col_type in columns:
                    raw_val = row.get(col_name, "")
                    if raw_val is None or raw_val.strip() == "":
                        values.append(None)
                    else:
                        try:
                            values.append(col_type(raw_val.strip()))
                        except (ValueError, TypeError):
                            values.append(raw_val.strip())
                rows_to_insert.append(values)

            conn.cursor().executemany(sql, rows_to_insert)

    def reset(self) -> None:
        """Reinicia a conexão e banco em memória (útil para testes unitários)."""
        if self._connection is not None:
            self._connection.close()
            self._connection = None


def get_db_connection() -> sqlite3.Connection:
    """Retorna uma conexão ativa ao banco de dados SQLite com os dados já carregados."""
    return DatabaseManager().get_connection()
