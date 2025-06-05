import json
import logging
from typing import Optional

import aiosqlite
import pandas as pd

from terminal_colors import TerminalColors as tc
from utilities import Utilities

DATA_BASE = "database/loans.db"

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class LoanData:
    conn: Optional[aiosqlite.Connection]

    def __init__(self: "LoanData", utilities: Utilities) -> None:
        self.conn = None
        self.utilities = utilities

    async def connect(self: "LoanData") -> None:
        db_uri = f"file:{self.utilities.shared_files_path}/{DATA_BASE}?mode=ro"

        try:
            self.conn = await aiosqlite.connect(db_uri, uri=True)
            logger.debug("Database connection opened.")
        except aiosqlite.Error as e:
            logger.exception("An error occurred", exc_info=e)
            self.conn = None

    async def close(self: "LoanData") -> None:
        if self.conn:
            await self.conn.close()
            logger.debug("Database connection closed.")

    async def _get_table_names(self: "LoanData") -> list:
        """Return a list of table names."""
        table_names = []
        async with self.conn.execute("SELECT name FROM sqlite_master WHERE type='table';") as tables:
            return [table[0] async for table in tables if table[0] != "sqlite_sequence"]

    async def _get_column_info(self: "LoanData", table_name: str) -> list:
        """Return a list of tuples containing column names and their types."""
        column_info = []
        async with self.conn.execute(f"PRAGMA table_info('{table_name}');") as columns:
            # col[1] is the column name, col[2] is the column type
            return [f"{col[1]}: {col[2]}" async for col in columns]

    async def _get_regions(self: "LoanData") -> list:
        """Return a list of unique regions in the database."""
        async with self.conn.execute("SELECT DISTINCT region FROM loan_products;") as regions:
            result = await regions.fetchall()
        return [region[0] for region in result]

    async def _get_product_types(self: "LoanData") -> list:
        """Return a list of unique product types in the database."""
        async with self.conn.execute("SELECT DISTINCT loan_type FROM loan_products;") as product_types:
            result = await product_types.fetchall()
        return [product_type[0] for product_type in result]

    async def _get_product_categories(self: "LoanData") -> list:
        """Return a list of unique product categories in the database."""
        async with self.conn.execute("SELECT DISTINCT product_name FROM loan_products;") as product_categories:
            result = await product_categories.fetchall()
        return [product_category[0] for product_category in result]

    async def _get_loan_term(self: "LoanData") -> list:
        """Return a list of unique reporting years in the database."""
        async with self.conn.execute("SELECT DISTINCT loan_term FROM loan_products;") as reporting_years:
            result = await reporting_years.fetchall()
        return [str(reporting_year[0]) for reporting_year in result]

    async def get_database_info(self: "LoanData") -> str:
        """Return a string containing the database schema information and common query fields."""
        table_dicts = []
        for table_name in await self._get_table_names():
            columns_names = await self._get_column_info(table_name)
            table_dicts.append(
                {"table_name": table_name, "column_names": columns_names})

        database_info = "\n".join(
            [
                f"Table {table['table_name']} Schema: Columns: {', '.join(table['column_names'])}"
                for table in table_dicts
            ]
        )
        regions = await self._get_regions()
        product_types = await self._get_product_types()
        product_categories = await self._get_product_categories()
        loan_terms = await self._get_loan_term()

        database_info += f"\nRegions: {', '.join(regions)}"
        database_info += f"\nProduct Types: {', '.join(product_types)}"
        database_info += f"\nProduct Categories: {', '.join(product_categories)}"
        database_info += f"\nLoan Terms: {', '.join(loan_terms)}"
        database_info += "\n\n"

        return database_info

    async def async_fetch_loan_data_using_sqlite_query(self: "LoanData", sqlite_query: str) -> str:
        """
        This function is used to answer user questions about Contoso loan data by executing SQLite queries against the database.

        :param sqlite_query: The input should be a well-formed SQLite query to extract information based on the user's question. The query result will be returned as a JSON object.
        :return: Return data in JSON serializable format.
        :rtype: str
        """

        print(
            f"\n{tc.BLUE}Function Call Tools: async_fetch_loans_data_using_sqlite_query{tc.RESET}\n")
        print(f"{tc.BLUE}Executing query: {sqlite_query}{tc.RESET}\n")

        try:
            # Perform the query asynchronously
            async with self.conn.execute(sqlite_query) as cursor:
                rows = await cursor.fetchall()
                columns = [description[0]
                           for description in cursor.description]

            if not rows:  # No need to create DataFrame if there are no rows
                return json.dumps("The query returned no results. Try a different question.")
            data = pd.DataFrame(rows, columns=columns)
            return data.to_json(index=False, orient="split")

        except Exception as e:
            return json.dumps({"SQLite query failed with error": str(e), "query": sqlite_query})
