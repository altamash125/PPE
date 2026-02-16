from setuptools import setup, find_packages

setup(
    name="ppecon_erp",
    version="0.0.1",           # Match __version__ in __init__.py
    description="PPE",
    packages=find_packages(),    # Finds ppecon_erp package
    include_package_data=True,
    install_requires=[
        # Only external python packages
    ],
)
