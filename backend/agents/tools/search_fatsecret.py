"""
FatSecret Indonesia Food Nutrition Scraper

A web scraper tool for extracting nutritional information from FatSecret Indonesia.
"""

from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlencode
import re

import requests
from bs4 import BeautifulSoup


@dataclass
class FoodNutrition:
    """Data class representing nutritional information for a food item."""

    name: str
    brand: Optional[str]
    serving_size: str
    calories: float
    fat: float
    carbs: float
    protein: float
    url: str

    def __repr__(self) -> str:
        brand_info = f" ({self.brand})" if self.brand else ""
        return (
            f"{self.name}{brand_info}\n"
            f"  Serving: {self.serving_size}\n"
            f"  Calories: {self.calories}kkal | Fat: {self.fat}g | "
            f"Carbs: {self.carbs}g | Protein: {self.protein}g"
        )


class FatSecretScraper:
    """Scraper for FatSecret Indonesia food database."""

    BASE_URL = "https://www.fatsecret.co.id"
    SEARCH_PATH = "/kalori-gizi/search"

    def __init__(self, timeout: int = 10):
        """
        Initialize the scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def search_food(self, keyword: str) -> list[FoodNutrition]:
        """
        Search for food items and extract their nutritional information.

        Args:
            keyword: Food name to search for (e.g., 'Bubur Ayam')

        Returns:
            List of FoodNutrition objects containing nutritional data

        Raises:
            requests.RequestException: If the HTTP request fails
            ValueError: If the response cannot be parsed
        """
        url = self._build_search_url(keyword)

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to fetch data from {url}: {e}")

        return self._parse_search_results(response.text)

    def _build_search_url(self, keyword: str) -> str:
        """Construct the search URL with proper encoding."""
        params = {"q": keyword}
        query_string = urlencode(params)
        return f"{self.BASE_URL}{self.SEARCH_PATH}?{query_string}"

    def _parse_search_results(self, html: str) -> list[FoodNutrition]:
        """
        Parse HTML and extract food nutritional information.

        Args:
            html: Raw HTML content from the search results page

        Returns:
            List of parsed FoodNutrition objects
        """
        soup = BeautifulSoup(html, "html.parser")
        results = []

        # Find the search results table
        search_table = soup.find("table", class_="generic searchResult")
        if not search_table:
            return results

        # Process each result row
        for row in search_table.find_all("tr"):
            try:
                food_info = self._parse_food_row(row)
                if food_info:
                    results.append(food_info)
            except Exception as e:
                # Log and continue if a single row fails
                print(f"Warning: Failed to parse row: {e}")
                continue

        return results

    def _parse_food_row(self, row) -> Optional[FoodNutrition]:
        """
        Parse a single table row to extract food information.

        Args:
            row: BeautifulSoup tag representing a table row

        Returns:
            FoodNutrition object or None if parsing fails
        """
        cell = row.find("td", class_="borderBottom")
        if not cell:
            return None

        # Extract food name and URL
        name_link = cell.find("a", class_="prominent")
        if not name_link:
            return None

        name = name_link.get_text(strip=True)
        url = self.BASE_URL + name_link.get("href", "")

        # Extract brand if present
        brand_link = cell.find("a", class_="brand")
        brand = brand_link.get_text(strip=True) if brand_link else None

        # Extract nutritional information
        info_div = cell.find("div", class_="smallText")
        if not info_div:
            return None

        info_text = info_div.get_text(strip=True)

        # Parse serving size and nutritional values
        nutrition = self._extract_nutrition_values(info_text)
        if not nutrition:
            return None

        return FoodNutrition(name=name, brand=brand, url=url, **nutrition)

    def _extract_nutrition_values(self, text: str) -> Optional[dict]:
        """
        Extract nutritional values from the info text.

        Args:
            text: Text containing nutritional information

        Returns:
            Dictionary with serving_size, calories, fat, carbs, protein
        """
        # Pattern: per [serving] - Kalori: XXXkkal | Lemak: XXg | Karb: XXg | Prot: XXg
        pattern = r"per (.+?) - Kalori: ([\d.,]+)kkal \| Lemak: ([\d.,]+)g \| Karb: ([\d.,]+)g \| Prot: ([\d.,]+)g"
        match = re.search(pattern, text)

        if not match:
            return None

        serving_size, calories, fat, carbs, protein = match.groups()

        return {
            "serving_size": serving_size.strip(),
            "calories": self._parse_float(calories),
            "fat": self._parse_float(fat),
            "carbs": self._parse_float(carbs),
            "protein": self._parse_float(protein),
        }

    @staticmethod
    def _parse_float(value: str) -> float:
        """Parse a float value, handling Indonesian number format."""
        # Replace comma with dot for decimal separator
        return float(value.replace(",", "."))


def scrape_food_nutrition(keyword: str) -> list[FoodNutrition]:
    """
    Convenience function to search for food nutritional information.

    Args:
        keyword: Food name to search for

    Returns:
        List of FoodNutrition objects

    Example:
        >>> results = scrape_food_nutrition('Bubur Ayam')
        >>> for food in results:
        ...     print(food)
    """
    scraper = FatSecretScraper()
    return scraper.search_food(keyword)


# Example usage
if __name__ == "__main__":
    # Search for a food item
    keyword = "Bubur Ayam"
    print(f"Searching for: {keyword}\n")

    try:
        results = scrape_food_nutrition(keyword)

        print(f"Found {len(results)} results:\n")
        for i, food in enumerate(results, 1):
            print(f"{i}. {food}")
            print()

    except Exception as e:
        print(f"Error: {e}")
