"""Consolidated debugging tool for HS Agent classification system.

This tool combines all debugging functionality into a single script with command-line options.
Replaces: debug_full_flow.py, debug_computer*.py, debug_search.py, debug_6digit.py,
          debug_candidates.py, debug_flow.py
"""

import asyncio
import argparse
from typing import Optional
from hs_agent.core.data_loader import HSDataLoader
from hs_agent.agents.traditional.classifier import HSClassifier
from hs_agent.core.models import ClassificationLevel


class DebugTool:
    """Consolidated debugging tool for HS classification system."""

    def __init__(self):
        self.loader = HSDataLoader()
        self.loader.load_all_data()
        print(f"📊 Data loaded: {len(self.loader.codes_6digit)} 6-digit codes")

    def debug_search(self, query: str, level: int = 2, limit: int = 5):
        """Debug search functionality."""
        print(f"\n=== SEARCH DEBUG ===")
        print(f"Query: '{query}' at {level}-digit level")

        results = self.loader.search_codes_by_description(query, level, limit=limit)
        print(f"Found {len(results)} results:")
        for i, (code, hs_code, score) in enumerate(results, 1):
            print(f"  {i}. {code}: {hs_code.description} (score: {score:.2f})")

        # Show what codes contain the search terms
        all_codes = self.loader.get_codes_by_level(level)
        search_lower = query.lower()
        matching_codes = []

        for code, hs_code in all_codes.items():
            if any(term in hs_code.description.lower() for term in search_lower.split()):
                matching_codes.append((code, hs_code))

        if matching_codes:
            print(f"\nAll {level}-digit codes containing search terms:")
            for code, hs_code in matching_codes[:10]:  # Limit to 10
                print(f"  {code}: {hs_code.description}")
        else:
            print(f"\nNo {level}-digit codes contain the search terms directly")

    def debug_candidates(self, query: str):
        """Debug candidate selection across all levels."""
        print(f"\n=== CANDIDATE DEBUG ===")
        print(f"Product: '{query}'")

        # Test each level
        for level, level_name in [(2, "CHAPTER"), (4, "HEADING"), (6, "SUBHEADING")]:
            print(f"\n{level_name} LEVEL ({level}-digit):")
            candidates = self.loader.search_codes_by_description(query, level, limit=5)
            print(f"Found {len(candidates)} candidates:")
            for i, (code, hs_code, score) in enumerate(candidates, 1):
                desc = hs_code.description[:60] + "..." if len(hs_code.description) > 60 else hs_code.description
                print(f"  {i}. {code}: {desc} (score: {score:.2f})")

    def debug_hierarchy(self, parent_code: str):
        """Debug hierarchical relationships for a given code."""
        print(f"\n=== HIERARCHY DEBUG ===")
        print(f"Parent code: {parent_code}")

        level = len(parent_code)
        if level == 2:
            # Show 4-digit codes under this chapter
            all_4digit = self.loader.get_codes_by_level(4)
            children = {code: hs_code for code, hs_code in all_4digit.items() if code.startswith(parent_code)}
            print(f"\n4-digit codes under chapter {parent_code}:")
        elif level == 4:
            # Show 6-digit codes under this heading
            all_6digit = self.loader.get_codes_by_level(6)
            children = {code: hs_code for code, hs_code in all_6digit.items() if code.startswith(parent_code)}
            print(f"\n6-digit codes under heading {parent_code}:")
        else:
            print(f"Invalid parent code length: {level}")
            return

        print(f"Found {len(children)} child codes:")
        for i, (code, hs_code) in enumerate(list(children.items())[:15], 1):  # Show first 15
            desc = hs_code.description[:60] + "..." if len(hs_code.description) > 60 else hs_code.description
            print(f"  {i}. {code}: {desc}")

        if len(children) > 15:
            print(f"  ... and {len(children) - 15} more")

    def debug_flow(self, query: str, detailed: bool = False):
        """Debug the complete classification flow."""
        print(f"\n=== CLASSIFICATION FLOW DEBUG ===")
        print(f"Product: '{query}'")

        # Step 1: Chapter level
        print(f"\n1. CHAPTER LEVEL (2-digit)")
        chapter_candidates = self.loader.search_codes_by_description(query, 2, limit=10)
        print(f"Found {len(chapter_candidates)} candidates:")
        for i, (code, hs_code, score) in enumerate(chapter_candidates[:5], 1):
            desc = hs_code.description[:50] + "..." if len(hs_code.description) > 50 else hs_code.description
            print(f"  {i}. {code}: {desc} (score: {score:.2f})")

        if not chapter_candidates:
            print("❌ No chapter candidates found!")
            return

        selected_chapter = chapter_candidates[0][0]
        print(f"✅ Selected chapter: {selected_chapter}")

        # Step 2: Heading level
        print(f"\n2. HEADING LEVEL (4-digit) with parent: {selected_chapter}")
        all_4digit = self.loader.get_codes_by_level(4)
        filtered_4digit = {code: hs_code for code, hs_code in all_4digit.items() if code.startswith(selected_chapter)}

        print(f"Available 4-digit codes under chapter {selected_chapter}: {len(filtered_4digit)}")

        if len(filtered_4digit) == 0:
            print("❌ No 4-digit codes found under selected chapter!")
            return

        # Search within filtered codes (what it SHOULD do)
        heading_matches = []
        query_lower = query.lower()
        for code, hs_code in filtered_4digit.items():
            desc_lower = hs_code.description.lower()
            score = sum(1.0 for word in query_lower.split() if word in desc_lower)

            if detailed:
                # Enhanced scoring based on product type
                if any(term in query_lower for term in ['computer', 'laptop']):
                    if any(term in desc_lower for term in ['processing', 'computer', 'data']):
                        score += 3.0
                elif any(term in query_lower for term in ['horse', 'mare', 'breeding']):
                    if any(term in desc_lower for term in ['horse', 'animals', 'live']):
                        score += 3.0

            if score > 0:
                heading_matches.append((code, hs_code, score))

        heading_matches.sort(key=lambda x: x[2], reverse=True)
        print(f"Heading matches found: {len(heading_matches)}")
        for i, (code, hs_code, score) in enumerate(heading_matches[:5], 1):
            desc = hs_code.description[:50] + "..." if len(hs_code.description) > 50 else hs_code.description
            print(f"  {i}. {code}: {desc} (score: {score:.2f})")

        if not heading_matches:
            print("❌ No heading matches found!")
            return

        selected_heading = heading_matches[0][0]
        print(f"✅ Selected heading: {selected_heading}")

        # Step 3: Subheading level
        print(f"\n3. SUBHEADING LEVEL (6-digit) with parent: {selected_heading}")
        self.debug_hierarchy(selected_heading)

    async def debug_full_agent_flow(self, query: str, model_name: str = "gemini-2.0-flash-exp"):
        """Debug the complete agent classification flow."""
        print(f"\n=== FULL AGENT FLOW DEBUG ===")
        print(f"Product: '{query}'")
        print(f"Model: {model_name}")

        try:
            classifier = HSClassifier(data_dir="data", model_name=model_name)

            # Test chapter level
            print(f"\n1. Testing chapter level...")
            chapter_result = await classifier.agent.classify_at_level(
                query, ClassificationLevel.CHAPTER, top_k=10
            )
            print(f"Chapter result: {chapter_result.selected_code} (confidence: {chapter_result.confidence:.3f})")
            print(f"Reasoning: {chapter_result.reasoning[:100]}...")

            # Test heading level
            print(f"\n2. Testing heading level...")
            heading_result = await classifier.agent.classify_at_level(
                query, ClassificationLevel.HEADING,
                parent_code=chapter_result.selected_code, top_k=10
            )
            print(f"Heading result: {heading_result.selected_code} (confidence: {heading_result.confidence:.3f})")
            print(f"Reasoning: {heading_result.reasoning[:100]}...")

            # Test subheading level
            print(f"\n3. Testing subheading level...")
            subheading_result = await classifier.agent.classify_at_level(
                query, ClassificationLevel.SUBHEADING,
                parent_code=heading_result.selected_code, top_k=10
            )
            print(f"Subheading result: {subheading_result.selected_code} (confidence: {subheading_result.confidence:.3f})")
            print(f"Reasoning: {subheading_result.reasoning[:100]}...")

            print(f"\n✅ FINAL RESULT: {subheading_result.selected_code}")

        except Exception as e:
            print(f"❌ Error in agent flow: {e}")
            import traceback
            traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="HS Agent Debug Tool")
    parser.add_argument('command', choices=['search', 'candidates', 'hierarchy', 'flow', 'agent'],
                       help='Debug command to run')
    parser.add_argument('query', help='Query string or code to debug')
    parser.add_argument('--level', type=int, default=2, choices=[2, 4, 6],
                       help='HS code level for search (default: 2)')
    parser.add_argument('--limit', type=int, default=5,
                       help='Limit number of results (default: 5)')
    parser.add_argument('--detailed', action='store_true',
                       help='Enable detailed analysis')
    parser.add_argument('--model', default='gemini-2.0-flash-exp',
                       help='Model name for agent testing')

    args = parser.parse_args()

    debug_tool = DebugTool()

    if args.command == 'search':
        debug_tool.debug_search(args.query, args.level, args.limit)
    elif args.command == 'candidates':
        debug_tool.debug_candidates(args.query)
    elif args.command == 'hierarchy':
        debug_tool.debug_hierarchy(args.query)
    elif args.command == 'flow':
        debug_tool.debug_flow(args.query, args.detailed)
    elif args.command == 'agent':
        asyncio.run(debug_tool.debug_full_agent_flow(args.query, args.model))


if __name__ == "__main__":
    main()