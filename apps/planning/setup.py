from setuptools import setup, find_packages

setup(
    name='planning',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    include_package_data=True,
    # Note: Most dependencies are defined in the root requirements.txt
    # This only lists planning-specific dependencies with flexible constraints
    install_requires=[
        'Flask>=2.0.0',
        'pandas>=2.0.0',
        'pyxlsb>=1.0.0',
        'requests>=2.0.0',
    ],
    description='Planning application as a Flask Blueprint',
    author='Your Name',
    author_email='your.email@example.com',
    url='http://your-project-url.com',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.9',
)
