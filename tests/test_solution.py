#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pathlib import Path
import unittest
import sys

# Insert the parent directory to sys path so schem is accessible even if it's not available system-wide
sys.path.insert(1, str(Path(__file__).parent.parent))

import schem
from schem.solution import Solution
import test_data

num_subtests = 0


def iter_test_data(solution_codes):
    global num_subtests
    for solution_code in solution_codes:
        num_subtests += 1

        # Parse only the metadata line so we can error out from the appropriate subTest if the full parse fails
        level_name, _, _, solution_name = schem.Solution.parse_metadata(solution_code)
        test_id = f'{level_name} - {solution_name}' if solution_name is not None else level_name
        level_code = schem.levels[level_name] if level_name in schem.levels else test_data.test_levels[level_name]

        yield test_id, level_code, solution_code


class TestSolution(unittest.TestCase):
    def test_parse_metadata_valid(self):
        """Tests for valid solution metadata lines."""
        in_out_cases = [("SOLUTION:level_name,author,0-0-0", ("level_name", "author", None, None)),
                        ("SOLUTION:level_name,author,1-0-0", ("level_name", "author", (1, 0, 0), None)),
                        ("SOLUTION:level_name,author,0-0-0,soln_name", ("level_name", "author", None, "soln_name")),
                        ("SOLUTION:'commas,in,level,name',author,0-0-0,soln_name",
                         ("commas,in,level,name", "author", None, "soln_name")),
                        ("SOLUTION:trailing_field_quote',author,0-0-0,soln_name",
                         ("trailing_field_quote'", "author", None, "soln_name")),
                        ("SOLUTION:level_name,'commas,in,author,name',0-0-0,soln_name",
                         ("level_name", "commas,in,author,name", None, "soln_name")),
                        ("SOLUTION:level_name,author,0-0-0,unquoted,commas,in,soln name",
                         ("level_name", "author", None, "unquoted,commas,in,soln name")),
                        ("SOLUTION:quote_in_soln_name,author,0-0-0,''''",
                         ("quote_in_soln_name", "author", None, "'")),
                        ("SOLUTION:level_name,author,0-0-0,'comma , and quote '' in soln name'",
                         ("level_name", "author", None, "comma , and quote ' in soln name"))]

        for in_str, expected_outs in in_out_cases:
            with self.subTest(msg=in_str):
                self.assertEqual(tuple(Solution.parse_metadata(in_str)), expected_outs)

    def test_parse_metadata_invalid(self):
        """Tests for invalid solution metadata lines which should raise an exception."""
        invalid_cases = ("SOLUTION:level_name,'unescaped_leading_quote,0-0-0",)

        for invalid_metadata in invalid_cases:
            with self.subTest(msg=invalid_metadata):
                with self.assertRaises(Exception):
                    Solution.parse_metadata(invalid_metadata)

    def test_parse_metadata_legacy_formats(self):
        """Tests for solution metadata lines that were valid in legacy SC or community tools."""
        in_out_cases = [("SOLUTION:commas,in,level,name,author,0-0-0,soln_name", ("commas,in,level,name", "author", None, "soln_name")),
                        ("SOLUTION:level_name,author,Incomplete-0-0,soln_name", ("level_name", "author", None, "soln_name"))]

        for in_str, expected_outs in in_out_cases:
            with self.subTest(msg=in_str):
                self.assertEqual(tuple(Solution.parse_metadata(in_str)), expected_outs)

    def test_init_errors(self):
        '''Tests for solutions that shouldn't import successfully.'''
        for test_id, level_code, solution_code in iter_test_data(test_data.import_errors):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                with self.assertRaises(schem.SolutionImportError):
                    schem.Solution(level, solution_code)
                print(f"✅  {test_id}")

    def test_run_missing_score(self):
        """Test that run() does not require an expected score."""
        for test_id, level_code, solution_code in iter_test_data(test_data.missing_score):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                solution.run()
                print(f"✅  {test_id}")

    def test_run_wrong_score(self):
        """Test that run() ignores whether the score does not match expected."""
        for test_id, level_code, solution_code in iter_test_data(test_data.wrong_score):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                solution.run()
                print(f"✅  {test_id}")

    def test_run_runtime_collisions(self):
        '''Tests for solutions that should encounter errors when run.'''
        for test_id, level_code, solution_code in iter_test_data(test_data.runtime_collisions):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                with self.assertRaises(Exception):
                    solution.run()
                print(f"✅  {test_id}")

    def test_run_wall_collisions(self):
        '''Tests for solutions that should collide with a wall when run.'''
        for test_id, level_code, solution_code in iter_test_data(test_data.wall_collisions):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                with self.assertRaises(Exception) as context:
                    solution.run()
                self.assertTrue(' wall' in str(context.exception).lower())

                print(f"✅  {test_id}")

    def test_run_invalid_outputs(self):
        '''Tests for solutions that should produce an InvalidOutput error.'''
        for test_id, level_code, solution_code in iter_test_data(test_data.invalid_outputs):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                with self.assertRaises(schem.InvalidOutputError):
                    solution.run()
                    print(f"✅  {test_id}")

    def test_run_infinite_loops(self):
        '''Tests for solutions that should exceed run()'s timeout.'''
        for test_id, level_code, solution_code in iter_test_data(test_data.infinite_loops):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                with self.assertRaises(TimeoutError):  # TODO: schem.InfiniteLoopError
                    solution.run()
                print(f"✅  {test_id}")

    def test_run_pause(self):
        for test_id, level_code, solution_code in iter_test_data(test_data.pause_then_complete):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)

                # Run the solution and expect it to pause
                with self.assertRaises(schem.PauseException):
                    solution.run()

                # Make sure the displayed cycle on immediate pause matches SC's
                self.assertEqual(solution.cycle, 2, "Paused cycle does not match expected")

                # Make sure hitting run() again will complete the solution
                self.assertEqual(solution.run(), (154, 1, 11), "Solution failed to continue run after pause")

                print(f"✅  {test_id}")

    def test_validate_missing_score(self):
        """Test that validate() requires an expected score."""
        for test_id, level_code, solution_code in iter_test_data(test_data.missing_score):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                with self.assertRaises(ValueError):
                    solution.validate()
                print(f"✅  {test_id}")

    def test_validate_wrong_score(self):
        """Test that validate() rejects successful solutions if the wrong score is specified."""
        for test_id, level_code, solution_code in iter_test_data(test_data.wrong_score):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                with self.assertRaises(schem.ScoreError):
                    solution.validate()
                print(f"✅  {test_id}")

    def test_validate_valid_solutions(self):
        '''Tests for solutions that should run to completion and match the expected score.
        Also outputs runtime performance stats.
        '''
        for test_id, level_code, solution_code in iter_test_data(test_data.valid_solutions):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                solution.validate()
                print(f"✅  {test_id}")

    def test_sandbox(self):
        """Test sandbox solutions load correctly and run to timeout (since they have no output components)."""
        for test_id, level_code, solution_code in iter_test_data(test_data.sandbox_solutions):
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                with self.assertRaises(TimeoutError):
                    solution.run(max_cycles=100_000)
                print(f"✅  {test_id}")

    def test_reset(self):
        """Test that solutions can be re-run after calling reset(), and still validate correctly."""
        for test_id, level_code, solution_code in iter_test_data(test_data.valid_solutions):
            test_id = 'Reset ' + test_id
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                solution.run()
                solution.reset()
                solution.validate()
                print(f"✅  {test_id}")

    def test_export_str(self):
        """Test that solutions can be re-exported to string, and that the new string still validates correctly."""
        for test_id, level_code, solution_code in iter_test_data(test_data.valid_solutions):
            test_id = 'Export ' + test_id
            with self.subTest(msg=test_id):
                level = schem.Level(level_code)
                solution = schem.Solution(level, solution_code)
                soln_from_export = schem.Solution(level, solution.export_str())
                soln_from_export.validate()
                print(f"✅  {test_id}")


if __name__ == '__main__':
    unittest.main(verbosity=0, exit=False)
    print(f"Ran {num_subtests} subtests")
