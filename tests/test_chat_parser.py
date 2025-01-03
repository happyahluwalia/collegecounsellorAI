"""Unit tests for chat message parsing functionality"""
import unittest
from unittest.mock import patch, MagicMock
import re
import json
from components.chat import parse_and_render_message
import logging

logger = logging.getLogger(__name__)

# Sample LLM response from attached file
SAMPLE_LLM_RESPONSE = '''
### 1. National History Academy Summer Program
- **Description**: This program allows high school students to explore American history through field trips to iconic historical sites, engaging discussions, and project-based learning. It's a unique chance to live and learn history where it happened.
- **Website**: [National History Academy Summer Program](https://www.historycamp.com)

<actionable id="4f8c1e6e-3487-4f71-bf00-af4ea6ab0c45">Apply to the National History Academy Summer Program to experience American history through immersive field trips and discussions.</actionable>

### 2. Telluride Association Summer Program (TASP) 
- **Description**: TASP offers a six-week educational experience for high school juniors focused on critical thinking and intellectual inquiry. While not exclusively historical, many seminars delve deeply into historical themes and periods, led by college and university faculty.
- **Website**: [Telluride Association Summer Program (TASP)](https://www.tellurideassociation.org/our-programs/high-school-students/summer-program-juniors-tasp/)

<actionable id="ab5d4d5c-5b1c-45d5-8e73-af5e9a2a5e5d">Consider the Telluride Association Summer Program for an intellectually stimulating experience that includes deep historical inquiry.</actionable>

### 3. Stanford University Pre-Collegiate Summer Institutes
- **Description**: Stanford's summer programs include courses for students interested in history. These range from specific periods and regions to themes such as warfare, diplomacy, and cultural history, taught by Stanford faculty and scholars.
- **Website**: [Stanford Pre-Collegiate Summer Institutes](https://spcs.stanford.edu/programs)

<actionable id="d4741f0e-8a5e-42d5-828c-9a9a05b6a7f5">Explore Stanford University Pre-Collegiate Summer Institutes for courses in various historical themes and periods.</actionable>
'''

@patch('streamlit.container')
@patch('streamlit.columns')
@patch('streamlit.markdown')
@patch('streamlit.button')
class TestChatParser(unittest.TestCase):
    """Test cases for chat message parsing"""

    def setUp(self):
        """Set up test environment"""
        self.logger = logging.getLogger(__name__)
        self.actionable_items = [
            {
                "id": "4f8c1e6e-3487-4f71-bf00-af4ea6ab0c45",
                "text": "Apply to the National History Academy Summer Program to experience American history through immersive field trips and discussions.",
                "category": "Summer Programs",
                "year": "10th, 11th",
                "url": "https://www.historycamp.com"
            },
            {
                "id": "ab5d4d5c-5b1c-45d5-8e73-af5e9a2a5e5d",
                "text": "Consider the Telluride Association Summer Program for an intellectually stimulating experience that includes deep historical inquiry.",
                "category": "Summer Programs",
                "year": "11th",
                "url": "https://www.tellurideassociation.org/our-programs/high-school-students/summer-program-juniors-tasp/"
            },
            {
                "id": "d4741f0e-8a5e-42d5-828c-9a9a05b6a7f5",
                "text": "Explore Stanford University Pre-Collegiate Summer Institutes for courses in various historical themes and periods.",
                "category": "Summer Programs",
                "year": "9th, 10th, 11th",
                "url": "https://spcs.stanford.edu/programs"
            }
        ]

    def test_extract_actionable_items(self, mock_button, mock_markdown, mock_columns, mock_container):
        """Test if actionable items are correctly extracted from the content"""
        # Set up mocks
        mock_cols = [MagicMock(), MagicMock()]
        mock_columns.return_value = mock_cols
        mock_container.return_value.__enter__.return_value = MagicMock()

        # Extract actionable items using the regex from parse_and_render_message
        matches = re.findall(r'<actionable id="([^"]+)">(.*?)</actionable>', SAMPLE_LLM_RESPONSE, flags=re.DOTALL)

        self.assertEqual(len(matches), 3, "Should find exactly 3 actionable items")

        # Verify each actionable item
        expected_ids = [
            "4f8c1e6e-3487-4f71-bf00-af4ea6ab0c45",
            "ab5d4d5c-5b1c-45d5-8e73-af5e9a2a5e5d",
            "d4741f0e-8a5e-42d5-828c-9a9a05b6a7f5"
        ]

        for i, (item_id, text) in enumerate(matches):
            self.assertEqual(item_id, expected_ids[i], f"Actionable item {i+1} should have correct ID")
            self.assertEqual(text, self.actionable_items[i]["text"], f"Actionable item {i+1} should have correct text")

        # Call the actual function to test integration
        parse_and_render_message(SAMPLE_LLM_RESPONSE, self.actionable_items)

        # Verify that markdown was called for both regular text and actionable items
        self.assertTrue(mock_markdown.called, "Markdown should be called to render content")
        self.assertEqual(mock_container.call_count, 3, "Container should be created for each actionable item")

    def test_extract_regular_content(self, mock_button, mock_markdown, mock_columns, mock_container):
        """Test if regular content is correctly extracted and formatted"""
        # Remove actionable items to get regular content
        regular_text = re.sub(r'<actionable id="[^"]+">.*?</actionable>', '', SAMPLE_LLM_RESPONSE, flags=re.DOTALL)

        # Verify regular content contains important parts but not actionable tags
        self.assertTrue("### 1. National History Academy Summer Program" in regular_text)
        self.assertTrue("### 2. Telluride Association Summer Program (TASP)" in regular_text)
        self.assertTrue("### 3. Stanford University Pre-Collegiate Summer Institutes" in regular_text)
        self.assertTrue("**Description**" in regular_text)

        # Verify actionable content is removed
        self.assertNotIn("<actionable", regular_text)
        self.assertNotIn("</actionable>", regular_text)

        # Call the actual function to test integration
        parse_and_render_message(SAMPLE_LLM_RESPONSE, self.actionable_items)

        # Verify markdown was called to render the regular content
        self.assertTrue(mock_markdown.called, "Markdown should be called to render regular content")

if __name__ == '__main__':
    unittest.main()