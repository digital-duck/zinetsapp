import unittest

from zinets_vis import parse_markdown_to_tree_data

class TestMarkdownParser(unittest.TestCase):
    
    def test_empty_input(self):
        """Test handling of empty input."""
        result = parse_markdown_to_tree_data("")
        self.assertEqual(result, {"name": "", "children": []})
    
    def test_tab_indentation(self):
        """Test with tab indentation."""
        markdown = "日\n\t- 白（丿 + 日）\n\t\t- 伯（亻 + 白）\n\t- 晶(日 + 日 + 日)"
        result = parse_markdown_to_tree_data(markdown)
        
        # Verify the structure
        self.assertEqual(result["name"], "日")
        self.assertEqual(len(result["children"]), 2)
        self.assertEqual(result["children"][0]["name"], "白")
        self.assertEqual(result["children"][0]["decomposition"], "丿 + 日")
        self.assertEqual(len(result["children"][0]["children"]), 1)
        self.assertEqual(result["children"][0]["children"][0]["name"], "伯")
        self.assertEqual(result["children"][1]["name"], "晶")
        self.assertEqual(result["children"][1]["decomposition"], "日 + 日 + 日")
    
    def test_2space_indentation(self):
        """Test with 2-space indentation."""
        markdown = "水\n  - 冰\n    - 凉\n  - 海"
        result = parse_markdown_to_tree_data(markdown)
        
        # Verify the structure
        self.assertEqual(result["name"], "水")
        self.assertEqual(len(result["children"]), 2)
        self.assertEqual(result["children"][0]["name"], "冰")
        self.assertEqual(len(result["children"][0]["children"]), 1)
        self.assertEqual(result["children"][0]["children"][0]["name"], "凉")
        self.assertEqual(result["children"][1]["name"], "海")
    
    def test_4space_indentation(self):
        """Test with 4-space indentation."""
        markdown = "藻\n    - 艹\n    - 澡\n        - 氵\n        - 喿\n            - 品\n                    - 口\n                    - 口\n                    - 口\n            - 木"
        result = parse_markdown_to_tree_data(markdown)
        
        # Verify the structure
        self.assertEqual(result["name"], "藻")
        self.assertEqual(len(result["children"]), 2)
        self.assertEqual(result["children"][0]["name"], "艹")
        self.assertEqual(result["children"][1]["name"], "澡")
        self.assertEqual(len(result["children"][1]["children"]), 2)
        self.assertEqual(result["children"][1]["children"][1]["name"], "喿")
        self.assertEqual(len(result["children"][1]["children"][1]["children"]), 2)
        self.assertEqual(result["children"][1]["children"][1]["children"][0]["name"], "品")
        self.assertEqual(len(result["children"][1]["children"][1]["children"][0]["children"]), 3)
    
    def test_mixed_indentation(self):
        """Test with mixed indentation (spaces and tabs)."""
        markdown = "心\n\t- 想\n    - 愿\n\t    - 惟\n\t- 情"
        result = parse_markdown_to_tree_data(markdown)
        
        # Verify the structure
        self.assertEqual(result["name"], "心")
        self.assertEqual(len(result["children"]), 2)
        self.assertEqual(result["children"][0]["name"], "想")
        self.assertEqual(len(result["children"][0]["children"]), 1) 
        self.assertEqual(result["children"][0]["children"][0]["name"], "愿")
        self.assertEqual(len(result["children"][0]["children"][0]["children"]), 1)
        self.assertEqual(result["children"][0]["children"][0]["children"][0]["name"], "惟")
        self.assertEqual(result["children"][1]["name"], "情")
    
    def test_irregular_indentation(self):
        """Test with irregular indentation patterns."""
        markdown = "木\n   - 森\n      - 林\n         - 桐\n  - 板"
        result = parse_markdown_to_tree_data(markdown)
        
        # Verify the structure
        self.assertEqual(result["name"], "木")
        self.assertEqual(len(result["children"]), 2)
        self.assertEqual(result["children"][0]["name"], "森")
        self.assertEqual(len(result["children"][0]["children"]), 1)
        self.assertEqual(result["children"][0]["children"][0]["name"], "林")
        self.assertEqual(len(result["children"][0]["children"][0]["children"]), 1)
        self.assertEqual(result["children"][0]["children"][0]["children"][0]["name"], "桐")
        self.assertEqual(result["children"][1]["name"], "板")
    
    def test_chinese_parentheses(self):
        """Test with Chinese parentheses for decomposition."""
        markdown = "心\n  - 想（心 + 相）\n  - 情（心 + 青）"
        result = parse_markdown_to_tree_data(markdown)
        
        # Verify the structure
        self.assertEqual(result["name"], "心")
        self.assertEqual(len(result["children"]), 2)
        self.assertEqual(result["children"][0]["name"], "想")
        self.assertEqual(result["children"][0]["decomposition"], "心 + 相")
        self.assertEqual(result["children"][1]["name"], "情")
        self.assertEqual(result["children"][1]["decomposition"], "心 + 青")
    
    def test_english_parentheses(self):
        """Test with English parentheses for decomposition."""
        markdown = "日\n  - 白(radical + sun)\n  - 晶(triple sun)"
        result = parse_markdown_to_tree_data(markdown)
        
        # Verify the structure
        self.assertEqual(result["name"], "日")
        self.assertEqual(len(result["children"]), 2)
        self.assertEqual(result["children"][0]["name"], "白")
        self.assertEqual(result["children"][0]["decomposition"], "radical + sun")
        self.assertEqual(result["children"][1]["name"], "晶")
        self.assertEqual(result["children"][1]["decomposition"], "triple sun")
    
    def test_non_dash_lines(self):
        """Test handling of lines that don't start with dash."""
        markdown = "水\n  - 冰\n    This is a note about ice\n    - 凉\n  - 海"
        result = parse_markdown_to_tree_data(markdown)
        
        # Verify the structure ignores the non-dash line
        self.assertEqual(result["name"], "水")
        self.assertEqual(len(result["children"]), 2)
        self.assertEqual(result["children"][0]["name"], "冰")
        self.assertEqual(len(result["children"][0]["children"]), 1)
        self.assertEqual(result["children"][0]["children"][0]["name"], "凉")
        self.assertEqual(result["children"][1]["name"], "海")
    
    def test_inconsistent_indentation(self):
        """Test with inconsistent indentation levels."""
        markdown = "水\n  - 冰\n      - 凉\n    - 冻\n  - 海"
        result = parse_markdown_to_tree_data(markdown)
        
        # This tests how the parser handles skipping indentation levels
        self.assertEqual(result["name"], "水")
        self.assertEqual(len(result["children"]), 2)
        self.assertEqual(result["children"][0]["name"], "冰")
        self.assertTrue(
            (len(result["children"][0]["children"]) == 2) or  # If it treats both as children
            (len(result["children"][0]["children"]) == 1 and  # Or if it handles nesting
             len(result["children"][0]["children"][0]["children"]) == 1)
        )

if __name__ == "__main__":
    unittest.main()