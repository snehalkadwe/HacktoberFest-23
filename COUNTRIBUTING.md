# Contribution Rules📚:

- You are allowed to make pull requests that break the rules. We just merge it ;)
- Do NOT remove other content.
- Add your file to the Projects_By_Contributors file
- Styling/code can be pretty, ugly or stupid, big or small as long as it works
- Try to keep pull requests small to minimize merge conflicts


## Getting Started 🤩🤗:

- Fork this repo (button on top)
- Clone on your local machine

```terminal
git clone https://github.com/theravi04/HacktoberFest-23.git
```
- Navigate to project directory.
```terminal
cd Hacktoberfest2022
```

- Create a new Branch

```markdown
git checkout -b my-new-branch
```
- Add your Name to `Contributors\ContributorsList.js`
```markdown
git add .
```
- Commit your changes.

```markdown
git commit -m "Relevant message"
```
- Then push 
```markdown
git push origin my-new-branch
```


- Create a new pull request from your forked repository

<br>

## Avoid Conflicts {Syncing your fork}

An easy way to avoid conflicts is to add an 'upstream' for your git repo, as other PR's may be merged while you're working on your branch/fork.   

```terminal
git remote add upstream https://github.com/theravi04/HacktoberFest-23.git
```

You can verify that the new remote has been added by typing
```terminal
git remote -v
```

To pull any new changes from your parent repo simply run
```terminal
git merge upstream/master
```

This will give you any eventual conflicts and allow you to easily solve them in your repo. It's a good idea to use it frequently in between your own commits to make sure that your repo is up to date with its parent.