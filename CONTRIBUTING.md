<!-- markdownlint-disable MD029 -->

# Contributing Guidelines

Thank you for your interest in contributing to this project! I welcome all contributions, including bug reports, feature requests, documentation improvements, and code changes.

To ensure that your contributions can be processed quickly and easily, please follow these guidelines.

## Reporting Issues in the database

Reminder that I am merely building upon an existing work, and I won't fix any aspects of the database that are directly maintained by AMQ mods.  
This saves me a large amount of work, and it ensures my database is always in sync with the AMQ database, which I hope will allow it to be used in AMQ in the future.  
~~This is also why if you check the AMQ Discord, you will see an infinite amount of requests I've made to fix stuff on the AMQ database~~

What `I will` fix :

> - Missing `group members`
> - Missing `backing vocals` (e.g. "MON" in "Smith with MON", which is mostly "Smith" singing and "MON" doing the backing vocals)
> - Missing `performers`, aka people who plays the instruments and are famous for it (which are a WIP, so there are a lot of missing ones) (e.g. Lupintic Six, Yoshida Brothers, etc...)
> - Missing `composers, arrangers` (which are a WIP, so there are a lot of missing ones)
> - Two `people with the exact same name` and are considered the same person in the database (e.g. Minami from DomexKano and Minami [Kuribayashi])
> - The `same person with two different names` and is not yet considered the same person in the database (e.g Shiena Nishizawa / EXiNA)

If you have found one of these that needs to be fixed, you can contact me on Discord (`xSardine#8168`), help is very appreciated.  
I didn't implement any way to crowdsource the data yet, so I'm doing it manually.  

What `I will not` fix :

> - Missing songs
> - Errors, typo, inconsistencies in any of the string fields (anime names, artist names, song names, etc...)

Those are directly maintained by the AMQ mods, please contact them through the [AMQ Discord server](https://discord.gg/w4a3sbP) if you find any of those.
Requests for fixing the AMQ database needs to go in the channels `database-fixes` or `uploaded-song-reports` depending on the type of issue. Make sure to read carefully the pins in each of these channels, as an invalid requests will result in you being banned from these channels.

## Reporting Issues in the code

If you find a bug or have a suggestion for a feature, you can open a new [issue](https://github.com/xSardine/anisongDB-backend/issues/new).

When opening an issue:

> 1. Check the [issues](https://github.com/xSardine/anisongDB-backend/issues) and [pull requests](https://github.com/xSardine/anisongDB-backend/pulls) to make sure that the feature/bug has not already been addressed, or is being worked upon.
> 2. Provide as much detail as possible about the issue, including steps to reproduce the issue if applicable.

## Submitting Pull Requests

I welcome contributions to this repository.  
Optimization to the search functions and improvement of code quality are especially welcomed.

If you want to contribute a feature, improve the code or fix a bug, please create a fork :

> 1. Check the [issues](https://github.com/xSardine/anisongDB-backend/issues) and [pull requests](https://github.com/xSardine/anisongDB-backend/pulls) to make sure that the feature/bug has not already been addressed, or is being worked upon.
> 2. Fork the repository and create a new branch for your changes.
> 3. Make the changes in your fork.

Optionally :

> 4. ***Add tests*** for your changes, if applicable.
> 5. ***Add documentation*** for your changes, if applicable.
> 6. Run the ***code formatter, linter and tests***. See the [Formatting, Linting and Testing](#formatting-linting-and-testing) section for more details.

I can take care of this for you if you want to contribute a feature or fix a bug, but don't want to go through the hassle

Open a pull request to this repository :

> 7. Open a pull request to this repository.
> 8. In the pull request description, explain the changes you have made and why they are necessary.

## Formatting, Linting and Testing

I use [black](https://pypi.org/project/black/) to format the code, [flake8](https://pypi.org/project/flake8/) to lint the code, and [pytest](https://pypi.org/project/pytest/) to run the tests.  
The file `.flake8` contain the configuration for flake8, which makes it compatible with black.

This repository use Poetry to manage dependencies and virtual environments.  
You can install all of these when running `poetry install` in the root of the repository.

You can then run these within the Poetry virtual environment by running `poetry run <command>` in the root of the repository :

- `poetry run black .` to format the code
- `poetry run flake8` to run the linter
- `poetry run pytest` to run the tests

Alternatively, you can install pre-commit hooks to automatically format, lint and test the code when you commit :  
To do so, run `poetry run pre-commit install` in the root of the repository.  
The commit will fail if the code is not formatted, linted correctly or do not pass the tests.

If you are using VSCode, you can also install the related extensions to automatically format and lint the code when you save a file.
