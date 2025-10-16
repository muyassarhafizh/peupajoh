"""
FatSecret Indonesia Detailed Nutrition Scraper

A web scraper tool for extracting detailed nutritional information from FatSecret Indonesia, automatically fetching detailed data from each food's "Informasi Gizi" page.
"""

from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlencode
import re
import asyncio

import httpx
from bs4 import BeautifulSoup


@dataclass
class DetailedNutrition:
    """Comprehensive nutritional information for a food item."""

    # Basic info
    name: str
    brand: Optional[str]
    url: str

    # Serving information
    serving_size: str
    serving_size_grams: Optional[float] = None

    # Main macronutrients
    calories: float = 0.0
    energy_kj: Optional[float] = None
    fat: float = 0.0
    carbs: float = 0.0
    protein: float = 0.0

    # Detailed fat breakdown
    saturated_fat: Optional[float] = None
    trans_fat: Optional[float] = None
    polyunsaturated_fat: Optional[float] = None
    monounsaturated_fat: Optional[float] = None

    # Other nutrients
    cholesterol: Optional[float] = None
    sodium: Optional[float] = None
    potassium: Optional[float] = None
    fiber: Optional[float] = None
    sugar: Optional[float] = None

    # Additional serving sizes
    alternative_servings: list[dict] = field(default_factory=list)

    def __repr__(self) -> str:
        brand_info = f" ({self.brand})" if self.brand else ""
        result = [
            f"{self.name}{brand_info}",
            f"  Serving: {self.serving_size}",
            f"  Calories: {self.calories}kkal",
            f"  Macros: Fat {self.fat}g | Carbs {self.carbs}g | Protein {self.protein}g",
        ]

        if self.saturated_fat:
            result.append(f"  Saturated Fat: {self.saturated_fat}g")
        if self.fiber:
            result.append(f"  Fiber: {self.fiber}g")
        if self.sodium:
            result.append(f"  Sodium: {self.sodium}mg")

        return "\n".join(result)


class FatSecretDetailedScraper:
    """Scraper for detailed FatSecret Indonesia nutritional information."""

    BASE_URL = "https://www.fatsecret.co.id"
    SEARCH_PATH = "/kalori-gizi/search"

    def __init__(self, timeout: int = 10):
        """
        Initialize the scraper.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def search_food(
        self, query: str, max_results: int = 10
    ) -> list[DetailedNutrition]:
        """
        Search for food items and fetch detailed nutritional information.

        Args:
            query: Food name to search for (e.g., 'Bubur Ayam')
            max_results: Maximum number of detailed results to fetch

        Returns:
            List of DetailedNutrition objects with comprehensive data

        Raises:
            httpx.HTTPError: If HTTP requests fail
        """
        url = self._build_search_url(query)

        try:
            response = await self.client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise httpx.HTTPError(f"Failed to fetch search results: {e}")

        # Get basic search results with URLs
        search_results = self._parse_search_results(response.text)

        # Fetch detailed info for each result concurrently
        detailed_results = []
        tasks = []
        for result in search_results[:max_results]:
            tasks.append(
                self._fetch_and_parse_detail_page(
                    result["url"], result["name"], result["brand"]
                )
            )

        # Gather all results, ignoring failures
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(
                    f"Warning: Failed to fetch details for {search_results[i]['name']}: {result}"
                )
            else:
                detailed_results.append(result)

        return detailed_results

    def _build_search_url(self, query: str) -> str:
        """Construct the search URL with proper encoding."""
        params = {"q": query}
        query_string = urlencode(params)
        return f"{self.BASE_URL}{self.SEARCH_PATH}?{query_string}"

    def _parse_search_results(self, html: str) -> list[dict]:
        """
        Parse search results to extract food names and detail page URLs.

        Args:
            html: Raw HTML from search results page

        Returns:
            List of dicts with name, brand, and url
        """
        soup = BeautifulSoup(html, "html.parser")
        results = []

        search_table = soup.find("table", class_="generic searchResult")
        if not search_table:
            return results

        for row in search_table.find_all("tr"):
            cell = row.find("td", class_="borderBottom")
            if not cell:
                continue

            # Extract food name and URL
            name_link = cell.find("a", class_="prominent")
            if not name_link:
                continue

            name = name_link.get_text(strip=True)
            url = self.BASE_URL + name_link.get("href", "")

            # Extract brand if present
            brand_link = cell.find("a", class_="brand")
            brand = brand_link.get_text(strip=True) if brand_link else None

            results.append({"name": name, "brand": brand, "url": url})

        return results

    async def _fetch_and_parse_detail_page(
        self, url: str, name: str, brand: Optional[str]
    ) -> DetailedNutrition:
        """
        Fetch and parse detailed nutrition page.

        Args:
            url: URL to the detail page
            name: Food name
            brand: Brand name if applicable

        Returns:
            DetailedNutrition object with comprehensive data
        """
        print(f"Fetching details for: {name}...")
        try:
            response = await self.client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise httpx.HTTPError(f"Failed to fetch {url}: {e}")

        return self._parse_nutrition_facts(response.text, name, brand, url)

    def _parse_nutrition_facts(
        self, html: str, name: str, brand: Optional[str], url: str
    ) -> DetailedNutrition:
        """
        Parse the nutrition facts from detail page.

        Args:
            html: Raw HTML content
            name: Food name
            brand: Brand name
            url: Page URL

        Returns:
            DetailedNutrition object with all extracted data
        """
        soup = BeautifulSoup(html, "html.parser")

        # Initialize nutrition object
        nutrition = DetailedNutrition(name=name, brand=brand, url=url, serving_size="")

        # Find the nutrition facts panel
        nutrition_panel = soup.find("div", class_="nutrition_facts")
        if not nutrition_panel:
            return nutrition

        # Extract serving size
        serving_elem = nutrition_panel.find("div", class_="serving_size_value")
        if serving_elem:
            serving_text = serving_elem.get_text(strip=True)
            nutrition.serving_size = serving_text

            # Extract grams from serving size (e.g., "1 porsi (240 g)")
            gram_match = re.search(r"\((\d+(?:[,.]\d+)?)\s*g\)", serving_text)
            if gram_match:
                nutrition.serving_size_grams = self._parse_float(gram_match.group(1))

        # Extract all nutrients using the nutrient divs
        nutrients = {}
        nutrient_divs = nutrition_panel.find_all("div", class_="nutrient")

        i = 0
        while i < len(nutrient_divs):
            div = nutrient_divs[i]

            # Check if this is a label (left-aligned)
            if "left" in div.get("class", []):
                label = div.get_text(strip=True)

                # Look for the corresponding value (right-aligned)
                if i + 1 < len(nutrient_divs):
                    next_div = nutrient_divs[i + 1]
                    if "right" in next_div.get("class", []):
                        value = next_div.get_text(strip=True)
                        nutrients[label] = value
                        i += 2
                        continue

            i += 1

        # Map Indonesian nutrient names to object attributes
        nutrition.energy_kj = self._extract_number(nutrients.get("Energi", ""))
        nutrition.calories = self._extract_number(
            nutrients.get("Energi", "").split("\n")[-1]
            if "\n" in nutrients.get("Energi", "")
            else nutrients.get("", "")
        )

        # Find calories more reliably
        for div in nutrient_divs:
            text = div.get_text(strip=True)
            if "kkal" in text:
                nutrition.calories = self._extract_number(text)
                break

        # Main macros
        nutrition.fat = self._extract_number(nutrients.get("Lemak", ""))
        nutrition.protein = self._extract_number(nutrients.get("Protein", ""))
        nutrition.carbs = self._extract_number(nutrients.get("Karbohidrat", ""))

        # Detailed fats
        nutrition.saturated_fat = self._extract_number(nutrients.get("Lemak Jenuh", ""))
        nutrition.trans_fat = self._extract_number(nutrients.get("Lemak Trans", ""))
        nutrition.polyunsaturated_fat = self._extract_number(
            nutrients.get("Lemak tak Jenuh Ganda", "")
        )
        nutrition.monounsaturated_fat = self._extract_number(
            nutrients.get("Lemak tak Jenuh Tunggal", "")
        )

        # Other nutrients
        nutrition.cholesterol = self._extract_number(nutrients.get("Kolesterol", ""))
        nutrition.sodium = self._extract_number(nutrients.get("Sodium", ""))
        nutrition.potassium = self._extract_number(nutrients.get("Kalium", ""))
        nutrition.fiber = self._extract_number(nutrients.get("Serat", ""))
        nutrition.sugar = self._extract_number(nutrients.get("Gula", ""))

        # Extract alternative serving sizes
        nutrition.alternative_servings = self._extract_serving_sizes(soup)

        return nutrition

    def _extract_serving_sizes(self, soup) -> list[dict]:
        """Extract alternative serving size options."""
        servings = []

        # Look for the serving sizes table
        serving_header = soup.find(
            "h4", string=lambda s: s and "Ukuran porsi umum" in s
        )
        if serving_header:
            table = serving_header.find_next("table", class_="generic")
            if table:
                for row in table.find_all("tr")[1:]:  # Skip header
                    cells = row.find_all("td")
                    if len(cells) >= 2:
                        size_cell = cells[0]
                        cal_cell = cells[1]

                        size_link = size_cell.find("a")
                        if size_link:
                            size_text = size_link.get_text(strip=True)
                            calories_text = cal_cell.get_text(strip=True)

                            servings.append(
                                {
                                    "size": size_text,
                                    "calories": self._extract_number(calories_text),
                                }
                            )

        return servings

    def _extract_number(self, text: str) -> Optional[float]:
        """Extract numeric value from text."""
        if not text:
            return None

        # Find first number in the text
        match = re.search(r"(\d+(?:[,.]\d+)?)", text)
        if match:
            return self._parse_float(match.group(1))
        return None

    @staticmethod
    def _parse_float(value: str) -> float:
        """Parse float value, handling Indonesian number format."""
        return float(value.replace(",", "."))


async def scrape_food_nutrition(
    query: str, max_results: int = 10
) -> list[DetailedNutrition]:
    """
    Search for food and get detailed nutritional information.

    Args:
        query: Food name to search for
        max_results: Maximum number of detailed results to fetch (default: 10)

    Returns:
        List of DetailedNutrition objects with comprehensive data

    Example:
        >>> results = await scrape_food_nutrition('Bubur Ayam')
        >>> for food in results:
        ...     print(f"{food.name}: {food.calories}kkal")
        ...     print(f"  Fat: {food.fat}g (Saturated: {food.saturated_fat}g)")
        ...     print(f"  Sodium: {food.sodium}mg")
    """
    async with FatSecretDetailedScraper() as scraper:
        return await scraper.search_food(query, max_results=max_results)


# Example usage
if __name__ == "__main__":

    async def main():
        query = "Bubur Ayam"

        print("=" * 70)
        print(f"DETAILED NUTRITION SEARCH: {query}")
        print("=" * 70)
        print()

        try:
            # Search and get detailed info for first 3 results
            results = await scrape_food_nutrition(query, max_results=3)

            print(f"Found {len(results)} detailed results:\n")

            for i, food in enumerate(results, 1):
                print(f"{i}. {food.name}" + (f" ({food.brand})" if food.brand else ""))
                print(f"   URL: {food.url}")
                print(f"   Serving: {food.serving_size}")
                if food.serving_size_grams:
                    print(f"   Gram dalam satu porsi: {food.serving_size_grams} grams")
                print()
                print("   MACRONUTRIENTS:")
                print(
                    f"   • Calories: {food.calories}kkal"
                    + (f" ({food.energy_kj}kj)" if food.energy_kj else "")
                )
                print(f"   • Fat: {food.fat}g")
                if food.saturated_fat:
                    print(f"     - Saturated: {food.saturated_fat}g")
                if food.trans_fat:
                    print(f"     - Trans: {food.trans_fat}g")
                if food.polyunsaturated_fat:
                    print(f"     - Polyunsaturated: {food.polyunsaturated_fat}g")
                if food.monounsaturated_fat:
                    print(f"     - Monounsaturated: {food.monounsaturated_fat}g")
                print(f"   • Carbohydrates: {food.carbs}g")
                if food.fiber:
                    print(f"     - Fiber: {food.fiber}g")
                if food.sugar:
                    print(f"     - Sugar: {food.sugar}g")
                print(f"   • Protein: {food.protein}g")
                print()

                if food.cholesterol or food.sodium or food.potassium:
                    print("   OTHER NUTRIENTS:")
                    if food.cholesterol:
                        print(f"   • Cholesterol: {food.cholesterol}mg")
                    if food.sodium:
                        print(f"   • Sodium: {food.sodium}mg")
                    if food.potassium:
                        print(f"   • Potassium: {food.potassium}mg")
                    print()

                if food.alternative_servings:
                    print("   ALTERNATIVE SERVINGS:")
                    for serving in food.alternative_servings[:3]:
                        print(f"   • {serving['size']}: {serving['calories']}kkal")
                    print()

                print("-" * 70)
                print()

        except Exception as e:
            print(f"Error: {e}")
            import traceback

            traceback.print_exc()

    asyncio.run(main())
