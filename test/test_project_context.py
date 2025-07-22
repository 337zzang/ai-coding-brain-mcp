"""
Unit tests for ProjectContext class

This module contains comprehensive unit tests for the ProjectContext class,
covering all methods, edge cases, and error conditions.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import os
import json

from ai_helpers_new.infrastructure.project_context import ProjectContext


class TestProjectContext:
    """Test suite for ProjectContext class"""

    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing"""
        temp_dir = tempfile.mkdtemp(prefix="test_project_")
        yield Path(temp_dir)
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def project_context(self, temp_project_dir):
        """Create a ProjectContext instance for testing"""
        return ProjectContext(temp_project_dir)

    # === Initialization Tests ===

    def test_init_valid_directory(self, temp_project_dir):
        """Test initialization with valid directory"""
        context = ProjectContext(temp_project_dir)
        assert context.root == temp_project_dir.resolve()
        assert context.ai_brain_dir.exists()
        assert context.backup_dir.exists()
        assert context.docs_dir.exists()

    def test_init_with_string_path(self, temp_project_dir):
        """Test initialization with string path"""
        context = ProjectContext(str(temp_project_dir))
        assert context.root == temp_project_dir.resolve()

    def test_init_nonexistent_directory(self):
        """Test initialization with non-existent directory"""
        with pytest.raises(ValueError, match="does not exist"):
            ProjectContext("/path/that/does/not/exist")

    def test_init_with_file_path(self, temp_project_dir):
        """Test initialization with file path instead of directory"""
        file_path = temp_project_dir / "test_file.txt"
        file_path.write_text("test")

        with pytest.raises(ValueError, match="is not a directory"):
            ProjectContext(file_path)

    # === Property Tests ===

    def test_path_properties(self, project_context):
        """Test all path properties"""
        root = project_context.root

        assert project_context.ai_brain_dir == root / ".ai-brain"
        assert project_context.flow_file == root / ".ai-brain" / "flows.json"
        assert project_context.current_flow_file == root / ".ai-brain" / "current_flow.txt"
        assert project_context.context_file == root / ".ai-brain" / "context.json"
        assert project_context.backup_dir == root / "backups"
        assert project_context.docs_dir == root / "docs"
        assert project_context.test_dir == root / "test"

    # === Directory Management Tests ===

    def test_ensure_directories(self, temp_project_dir):
        """Test directory creation"""
        # Remove directories if they exist
        for dir_name in [".ai-brain", "backups", "docs"]:
            dir_path = temp_project_dir / dir_name
            if dir_path.exists():
                shutil.rmtree(dir_path)

        context = ProjectContext(temp_project_dir)

        # Verify directories were created
        assert context.ai_brain_dir.exists()
        assert context.backup_dir.exists()
        assert context.docs_dir.exists()

    def test_ensure_directories_idempotent(self, project_context):
        """Test that ensure_directories is idempotent"""
        # Create some files in directories
        (project_context.ai_brain_dir / "test.txt").write_text("test")
        (project_context.backup_dir / "backup.txt").write_text("backup")

        # Call ensure_directories again
        project_context.ensure_directories()

        # Verify files still exist
        assert (project_context.ai_brain_dir / "test.txt").exists()
        assert (project_context.backup_dir / "backup.txt").exists()

    # === Path Conversion Tests ===

    def test_get_relative_path(self, project_context):
        """Test absolute to relative path conversion"""
        # Path within project
        abs_path = project_context.root / "subdir" / "file.txt"
        rel_path = project_context.get_relative_path(abs_path)
        assert rel_path == Path("subdir/file.txt")

        # Path outside project
        external_path = project_context.root.parent / "external.txt"
        result = project_context.get_relative_path(external_path)
        assert result == external_path  # Returns original path

    def test_get_absolute_path(self, project_context):
        """Test relative to absolute path conversion"""
        rel_path = "docs/README.md"
        abs_path = project_context.get_absolute_path(rel_path)
        assert abs_path == project_context.root / "docs" / "README.md"

        # Test with Path object
        rel_path_obj = Path("test/test_file.py")
        abs_path = project_context.get_absolute_path(str(rel_path_obj))
        assert abs_path == project_context.root / "test" / "test_file.py"

    def test_is_within_project(self, project_context):
        """Test project boundary checking"""
        # Paths within project
        assert project_context.is_within_project(project_context.root)
        assert project_context.is_within_project(project_context.root / "subdir")
        assert project_context.is_within_project(project_context.ai_brain_dir)

        # Paths outside project
        assert not project_context.is_within_project(project_context.root.parent)
        assert not project_context.is_within_project(Path("/tmp"))
        assert not project_context.is_within_project(Path.home())

    # === Project Info Tests ===

    def test_get_project_info(self, project_context):
        """Test project information retrieval"""
        info = project_context.get_project_info()

        assert info['root'] == str(project_context.root)
        assert info['name'] == project_context.root.name
        assert info['ai_brain_exists'] is True
        assert info['flows_exists'] is False  # No flows.json created yet
        assert info['has_git'] is False  # No .git directory
        assert info['has_backup'] is True
        assert info['has_docs'] is True

    def test_get_project_info_with_git(self, project_context):
        """Test project info with git repository"""
        # Create .git directory
        git_dir = project_context.root / ".git"
        git_dir.mkdir()

        info = project_context.get_project_info()
        assert info['has_git'] is True

    # === File Management Tests ===

    def test_get_ai_brain_files_empty(self, project_context):
        """Test getting AI brain files when empty"""
        files = project_context.get_ai_brain_files()
        assert isinstance(files, dict)
        assert len(files) == 0

    def test_get_ai_brain_files_with_content(self, project_context):
        """Test getting AI brain files with content"""
        # Create some test files
        (project_context.ai_brain_dir / "flows.json").write_text('{"flows": {}}')
        (project_context.ai_brain_dir / "context.json").write_text('{"events": []}')
        (project_context.ai_brain_dir / "current_flow.txt").write_text("flow_123")

        # Create a subdirectory (should be ignored)
        subdir = project_context.ai_brain_dir / "backups"
        subdir.mkdir()
        (subdir / "backup.json").write_text("{}")

        files = project_context.get_ai_brain_files()

        assert len(files) == 3  # Only files, not subdirectories
        assert "flows.json" in files
        assert "context.json" in files
        assert "current_flow.txt" in files
        assert files["flows.json"] > 0

    # === Backup Management Tests ===

    def test_clean_ai_brain_backups_no_backups(self, project_context):
        """Test cleaning backups when none exist"""
        # Should not raise any errors
        project_context.clean_ai_brain_backups(keep_count=5)

    def test_clean_ai_brain_backups_with_backups(self, project_context):
        """Test cleaning old backups"""
        backup_dir = project_context.ai_brain_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Create 15 backup files
        for i in range(15):
            backup_file = backup_dir / f"backup_{i:02d}.backup"
            backup_file.write_text(f"backup {i}")

        # Keep only 10
        project_context.clean_ai_brain_backups(keep_count=10)

        remaining_files = list(backup_dir.glob("*.backup"))
        assert len(remaining_files) == 10

        # Verify that the newest files are kept (higher numbers)
        remaining_names = [f.name for f in remaining_files]
        for i in range(5, 15):
            assert f"backup_{i:02d}.backup" in remaining_names

    # === Working Directory Tests ===

    def test_switch_to(self, project_context):
        """Test switching working directory"""
        original_cwd = Path.cwd()

        try:
            project_context.switch_to()
            assert Path.cwd() == project_context.root
        finally:
            # Always restore original directory
            os.chdir(original_cwd)

    # === String Representation Tests ===

    def test_str_representation(self, project_context):
        """Test string representation"""
        str_repr = str(project_context)
        assert str_repr == f"ProjectContext({project_context.root})"

    def test_repr_representation(self, project_context):
        """Test developer representation"""
        repr_str = repr(project_context)
        assert repr_str == f"ProjectContext(root='{project_context.root}')"

    # === Equality and Hashing Tests ===

    def test_equality(self, temp_project_dir):
        """Test equality comparison"""
        context1 = ProjectContext(temp_project_dir)
        context2 = ProjectContext(temp_project_dir)
        context3 = ProjectContext(temp_project_dir.parent)

        assert context1 == context2
        assert context1 != context3
        assert context1 != "not a ProjectContext"

    def test_hashing(self, temp_project_dir):
        """Test hashing for use in sets/dicts"""
        context1 = ProjectContext(temp_project_dir)
        context2 = ProjectContext(temp_project_dir)

        # Same path should have same hash
        assert hash(context1) == hash(context2)

        # Can be used in sets
        context_set = {context1, context2}
        assert len(context_set) == 1

        # Can be used as dict keys
        context_dict = {context1: "value1", context2: "value2"}
        assert len(context_dict) == 1
        assert context_dict[context1] == "value2"

    # === Edge Cases and Error Conditions ===

    def test_symlink_handling(self, temp_project_dir):
        """Test handling of symbolic links"""
        if os.name == 'nt':  # Windows
            pytest.skip("Symlink test skipped on Windows")

        # Create a symlink
        real_dir = temp_project_dir / "real"
        real_dir.mkdir()
        link_dir = temp_project_dir / "link"
        link_dir.symlink_to(real_dir)

        # ProjectContext should resolve to real path
        context = ProjectContext(link_dir)
        assert context.root == real_dir.resolve()

    def test_unicode_paths(self, temp_project_dir):
        """Test handling of unicode in paths"""
        unicode_dir = temp_project_dir / "测试目录"
        unicode_dir.mkdir()

        context = ProjectContext(unicode_dir)
        assert context.root.name == "测试目录"

        # Test file operations with unicode
        unicode_file = context.ai_brain_dir / "测试文件.json"
        unicode_file.write_text('{"test": "data"}', encoding='utf-8')

        files = context.get_ai_brain_files()
        assert "测试文件.json" in files

    def test_very_long_paths(self, temp_project_dir):
        """Test handling of very long paths"""
        # Create a deeply nested directory
        deep_path = temp_project_dir
        for i in range(10):
            deep_path = deep_path / f"level_{i}"
            deep_path.mkdir()

        context = ProjectContext(deep_path)
        assert context.root == deep_path.resolve()
        assert len(str(context.flow_file)) > 100  # Ensure it's a long path


class TestProjectContextIntegration:
    """Integration tests for ProjectContext with real file operations"""

    @pytest.fixture
    def real_project(self, tmp_path):
        """Create a realistic project structure"""
        # Create project structure
        (tmp_path / ".git").mkdir()
        (tmp_path / "python" / "src").mkdir(parents=True)
        (tmp_path / "docs").mkdir()
        (tmp_path / "test").mkdir()

        # Add some files
        (tmp_path / "README.md").write_text("# Test Project")
        (tmp_path / "python" / "src" / "main.py").write_text("print('Hello')")

        return tmp_path

    def test_real_project_structure(self, real_project):
        """Test with realistic project structure"""
        context = ProjectContext(real_project)

        info = context.get_project_info()
        assert info['has_git'] is True
        assert info['name'] == real_project.name

        # Test path conversions
        main_py = real_project / "python" / "src" / "main.py"
        rel_path = context.get_relative_path(main_py)
        assert rel_path == Path("python/src/main.py")

        # Test boundary checking
        assert context.is_within_project(main_py)
        assert not context.is_within_project(real_project.parent)


# === Test Utilities ===

def test_imports():
    """Test that all imports work correctly"""
    from ai_helpers_new.infrastructure.project_context import ProjectContext
    from ai_helpers_new.infrastructure import ProjectContext as PC

    assert ProjectContext is PC
