import importlib.util
import pathlib
import unittest


SCRIPT = pathlib.Path(__file__).parents[1] / "scripts" / "merge_bib.py"
SPEC = importlib.util.spec_from_file_location("merge_bib", SCRIPT)
merge_bib = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(merge_bib)


class MergeBibTests(unittest.TestCase):
    def test_sort_uses_explicit_year_before_key_suffix(self):
        text = (
            "@article{Later1990, title={Later}, journal={J}, year={2024}}\n"
            "@article{Earlier2030, title={Earlier}, journal={J}, year={2020}}\n"
        )
        result = merge_bib.sort_entries_in_text(text)
        self.assertLess(result.index("Earlier2030"), result.index("Later1990"))

    def test_sort_descending(self):
        text = (
            "@article{Old2020, title={Old}, journal={J}, year={2020}}\n"
            "@article{New2024, title={New}, journal={J}, year={2024}}\n"
        )
        result = merge_bib.sort_entries_in_text(text, "year-desc")
        self.assertLess(result.index("New2024"), result.index("Old2020"))

    def test_duplicate_keys_are_case_insensitive(self):
        text = "@misc{Same, title={A}}\n@misc{same, title={B}}\n"
        self.assertIn("same", merge_bib.find_duplicate_keys(text))

    def test_duplicate_doi_normalization(self):
        text = (
            "@article{A2020, title={A}, doi={10.1/ABC}}\n"
            "@article{B2021, title={B}, doi={https://doi.org/10.1/abc}}\n"
        )
        self.assertIn("10.1/abc", merge_bib.find_duplicate_identifiers(text, "doi"))

    def test_validation_requires_conference_year(self):
        text = "@inproceedings{A2020, title={A}, booktitle={Conf}}"
        self.assertTrue(any("year/date" in w for w in merge_bib.validate_entries(text)))


if __name__ == "__main__":
    unittest.main()
