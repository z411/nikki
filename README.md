# nikki
Simple static blog generator written in Python. It takes files written in Markdown and generates a static blog with it. It's currently under development.

## Requirements:
* Python 2 or 3
* Mistune
* wheezy_template

## Usage
Clone the repository, create the directory `pages` and add your markdown files (with the .md extension) inside. You can use subdirectories for different categories. Then just run nikki.py without arguments and your blog should be generated in the `output` directory.

## Planned
* Automatic copying of static files such as stylesheets and images
* Pagination
* Archive list
* Tags (maybe)
