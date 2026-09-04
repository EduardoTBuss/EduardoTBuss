"""Toolkit behind the profile README.

Split into one module per responsibility so that a change of intent touches a
single file: filesystem layout (paths), data access (datastore), contract
checking (validation), network (github_api), SVG drawing (stats_band) and
Markdown rendering (readme_blocks).
"""
