"""Integration tests for API endpoints with real classification scenarios.

Tests verify:
1. Endpoints return valid responses
2. Classification output is logical (format, confidence, codes)
3. Target classifications match expected HS codes
"""

import pytest
from fastapi.testclient import TestClient

from app import app

# Test client for API calls
client = TestClient(app)


# ========== Test Fixtures ==========


@pytest.fixture
def test_products():
    """Real product descriptions with expected HS code ranges.

    Each product includes:
    - description: The product to classify
    - expected_chapter: Expected 2-digit chapter
    - expected_code_prefix: Expected code prefix (to check if in right area)
    - rationale: Why this classification is expected
    """
    return [
        {
            "description": "laptop computer with 15 inch screen",
            "expected_chapter": "84",
            "expected_code_prefix": "8471",  # Automatic data processing machines
            "weirationale": "Laptops are classified under machinery (84), specifically data processing machines (8471)",
        },
        {
            "description": "cotton t-shirt for men",
            "expected_chapter": "61",
            "expected_code_prefix": "61",  # Knitted or crocheted apparel
            "rationale": "T-shirts are typically knitted garments, classified under chapter 61",
        },
        {
            "description": "fresh apples",
            "expected_chapter": "08",
            "expected_code_prefix": "08",  # Edible fruit and nuts
            "rationale": "Fresh fruit classified under chapter 08",
        },
        {
            "description": "wooden dining table",
            "expected_chapter": "94",
            "expected_code_prefix": "9403",  # Other furniture
            "rationale": "Furniture classified under chapter 94",
        },
        {
            "description": "pharmaceutical antibiotics tablets",
            "expected_chapter": "30",
            "expected_code_prefix": "30",  # Pharmaceutical products
            "rationale": "Medicaments classified under chapter 30",
        },
    ]


# ========== Single Classification Endpoint Tests ==========


class TestClassifyEndpoint:
    """Tests for POST /api/classify endpoint (single classification)."""

    def test_classify_endpoint_returns_valid_structure(self, test_products):
        """Test that classification endpoint returns valid response structure."""
        product = test_products[0]  # laptop computer

        response = client.post(
            "/api/classify", json={"product_description": product["description"]}
        )

        # Check response status
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()

        # Verify required fields exist
        assert "final_code" in data
        assert "overall_confidence" in data
        assert "chapter" in data
        assert "heading" in data
        assert "subheading" in data

        # Verify chapter structure
        chapter = data["chapter"]
        assert "selected_code" in chapter
        assert "confidence" in chapter
        assert "reasoning" in chapter
        assert "description" in chapter

    def test_classify_returns_logical_confidence_scores(self, test_products):
        """Test that confidence scores are in valid range [0.0, 1.0]."""
        product = test_products[0]

        response = client.post(
            "/api/classify", json={"product_description": product["description"]}
        )

        data = response.json()

        # Check overall confidence
        assert (
            0.0 <= data["overall_confidence"] <= 1.0
        ), f"Overall confidence {data['overall_confidence']} not in [0.0, 1.0]"

        # Check individual level confidences
        for level in ["chapter", "heading", "subheading"]:
            confidence = data[level]["confidence"]
            assert 0.0 <= confidence <= 1.0, f"{level} confidence {confidence} not in [0.0, 1.0]"

    def test_classify_returns_valid_hs_code_format(self, test_products):
        """Test that returned HS codes have valid format."""
        product = test_products[0]

        response = client.post(
            "/api/classify", json={"product_description": product["description"]}
        )

        data = response.json()

        # Final code should be 6 digits or special NO_HS_CODE
        final_code = data["final_code"]
        assert final_code == "000000" or (
            len(final_code) == 6 and final_code.isdigit()
        ), f"Invalid final code format: {final_code}"

        # Chapter code should be 2 digits
        chapter_code = data["chapter"]["selected_code"]
        assert (
            len(chapter_code) == 2 and chapter_code.isdigit()
        ), f"Invalid chapter code: {chapter_code}"

        # Heading code should be 4 digits
        heading_code = data["heading"]["selected_code"]
        assert (
            len(heading_code) == 4 and heading_code.isdigit()
        ), f"Invalid heading code: {heading_code}"

        # Subheading code should be 6 digits
        subheading_code = data["subheading"]["selected_code"]
        assert subheading_code == "000000" or (
            len(subheading_code) == 6 and subheading_code.isdigit()
        ), f"Invalid subheading code: {subheading_code}"

    @pytest.mark.parametrize("product_idx", [0, 1, 2, 3, 4])
    def test_classify_matches_expected_chapter(self, test_products, product_idx):
        """Test that classification returns expected chapter for various products."""
        product = test_products[product_idx]

        response = client.post(
            "/api/classify", json={"product_description": product["description"]}
        )

        data = response.json()
        chapter_code = data["chapter"]["selected_code"]

        # Check if chapter matches expected
        assert chapter_code == product["expected_chapter"], (
            f"Product '{product['description']}' classified to chapter {chapter_code}, "
            f"expected {product['expected_chapter']}. Rationale: {product['rationale']}"
        )

    @pytest.mark.parametrize("product_idx", [0, 1, 2, 3, 4])
    def test_classify_final_code_starts_with_expected_prefix(self, test_products, product_idx):
        """Test that final HS code starts with expected prefix."""
        product = test_products[product_idx]

        response = client.post(
            "/api/classify", json={"product_description": product["description"]}
        )

        data = response.json()
        final_code = data["final_code"]

        # Skip if no HS code found
        if final_code == "000000":
            pytest.skip("No HS code found for product")

        # Check if final code starts with expected prefix
        expected_prefix = product["expected_code_prefix"]
        assert final_code.startswith(expected_prefix), (
            f"Product '{product['description']}' classified to {final_code}, "
            f"expected prefix {expected_prefix}. Rationale: {product['rationale']}"
        )

    def test_classify_with_high_performance_mode(self, test_products):
        """Test classification with high_performance=True (wide net approach)."""
        product = test_products[0]

        response = client.post(
            "/api/classify",
            json={
                "product_description": product["description"],
                "high_performance": True,
                "max_selections": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should still return valid structure
        assert "final_code" in data
        assert "overall_confidence" in data

        # High performance mode may have higher confidence due to multi-path comparison
        assert data["overall_confidence"] > 0.0


# ========== Multi-Choice Classification Endpoint Tests ==========


class TestClassifyMultiEndpoint:
    """Tests for POST /api/classify/multi endpoint (multi-path classification)."""

    def test_classify_multi_returns_valid_structure(self, test_products):
        """Test that multi-choice endpoint returns valid response structure."""
        product = test_products[0]

        response = client.post(
            "/api/classify/multi",
            json={"product_description": product["description"], "max_selections": 3},
        )

        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "paths" in data
        assert "final_selected_code" in data
        assert "final_confidence" in data
        assert "comparison_summary" in data

        # Verify paths structure
        assert len(data["paths"]) >= 1, "Should return at least 1 path"

        first_path = data["paths"][0]
        assert "chapter_code" in first_path
        assert "heading_code" in first_path
        assert "subheading_code" in first_path
        assert "path_confidence" in first_path

    def test_classify_multi_respects_max_selections(self, test_products):
        """Test that multi-choice respects max_selections parameter."""
        product = test_products[0]
        max_sel = 2

        response = client.post(
            "/api/classify/multi",
            json={"product_description": product["description"], "max_selections": max_sel},
        )

        data = response.json()

        # Number of paths should be <= max_selections^3
        # (max_selections chapters × max_selections headings × max_selections subheadings)
        max_possible_paths = max_sel**3
        assert (
            len(data["paths"]) <= max_possible_paths
        ), f"Returned {len(data['paths'])} paths, expected <= {max_possible_paths}"

    def test_classify_multi_returns_best_path_in_final_code(self, test_products):
        """Test that final_selected_code is present in one of the paths."""
        product = test_products[0]

        response = client.post(
            "/api/classify/multi",
            json={"product_description": product["description"], "max_selections": 3},
        )

        data = response.json()
        final_code = data["final_selected_code"]

        # Skip if no code found
        if final_code == "000000":
            pytest.skip("No HS code found")

        # Final code should match one of the path subheadings
        path_codes = [path["subheading_code"] for path in data["paths"]]
        assert (
            final_code in path_codes
        ), f"Final code {final_code} not found in any path: {path_codes}"

    def test_classify_multi_paths_are_hierarchical(self, test_products):
        """Test that each path follows hierarchical structure (chapter → heading → subheading)."""
        product = test_products[0]

        response = client.post(
            "/api/classify/multi",
            json={"product_description": product["description"], "max_selections": 3},
        )

        data = response.json()

        for i, path in enumerate(data["paths"]):
            chapter = path["chapter_code"]
            heading = path["heading_code"]
            subheading = path["subheading_code"]

            # Heading should start with chapter
            assert heading.startswith(
                chapter
            ), f"Path {i}: heading {heading} doesn't start with chapter {chapter}"

            # Subheading should start with heading (unless it's 000000)
            if subheading != "000000":
                assert subheading.startswith(
                    heading
                ), f"Path {i}: subheading {subheading} doesn't start with heading {heading}"


# ========== Error Handling Tests ==========


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_classify_with_empty_description(self):
        """Test that empty product description is handled gracefully."""
        response = client.post("/api/classify", json={"product_description": ""})

        # Should return 422 Validation Error or 200 with edge case handling
        assert response.status_code in [200, 422]

        if response.status_code == 200:
            data = response.json()
            # May return NO_HS_CODE (000000), Chapter 99 (unclassifiable), or other edge case
            # Chapter 99: "Commodities not specified according to kind"
            assert (
                data["final_code"].startswith("99") or data["final_code"] == "000000"
            ), f"Expected edge case code (99xxxx or 000000), got {data['final_code']}"

    def test_classify_with_very_ambiguous_product(self):
        """Test classification with very ambiguous product description."""
        response = client.post("/api/classify", json={"product_description": "thing"})

        # Should still return valid response
        assert response.status_code == 200
        data = response.json()

        # Confidence may be lower for ambiguous products
        assert "overall_confidence" in data
        # But should still have a structure
        assert "chapter" in data

    def test_classify_multi_with_invalid_max_selections(self):
        """Test that invalid max_selections is handled."""
        response = client.post(
            "/api/classify/multi",
            json={
                "product_description": "laptop",
                "max_selections": 0,  # Invalid - must be >= 1
            },
        )

        # Should return validation error
        assert response.status_code == 422


# ========== Health Check Tests ==========


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_ok(self):
        """Test that health check endpoint returns successfully."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert data["status"] in ["ok", "healthy"]
