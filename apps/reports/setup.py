from setuptools import setup, find_packages

setup(
    name="reports",
    version="1.0.0",
    description="Reports module for mockCMMS",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask>=2.0.0",
        "Flask-SQLAlchemy>=3.0.0",
    ],
    python_requires=">=3.8",
)
