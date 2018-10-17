# Ways of Working

There are particular ways that this team is attempting to develop `rp-sidekick`. This section documents those processes.

## Rebasing
In this code base, we enforce [rebasing on GH](https://help.github.com/articles/configuring-commit-rebasing-for-pull-requests/) instead of merging your commits. This document does not attempt to explain rebasing. Please see [here](https://www.atlassian.com/git/tutorials/merging-vs-rebasing) for an explanation. In brief, however, if no additional commits have been added to the `develop` branch while you have been working on a feature, this should not be an issue for you, and Github will simply offer you the option to Rebase and Merge within the PR. However, if it detects merge conflicts, you will need to make sure that your branch is rebased manually and deal with the merge conflicts before merging it in to the `develop` branch (i.e. as though you made your changes on top of the latest changes in the develop branch).

Locally, you can do this with:
```
$ git rebase develop
```
Then solve the merge conflicts and other nastiness and run:
```
$ git rebase --continue
```
Please feel free to reach out to the maintainers of this project to help you through this if you're not comfortable.

Once you're satsfied with local changes, you can overwrite your PR branch with the following:
```
git push --force-with-lease
```
