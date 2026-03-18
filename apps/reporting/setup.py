from setuptools import find_packages, setup

setup(
    name="reporting",
    version="1.0.0",
    description="Reporting module for mockCMMS",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask>=2.0.0",
        "Flask-SQLAlchemy>=3.0.0",
    ],
    python_requires=">=3.8",
)
