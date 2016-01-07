# ec2-alfred-workflow

An Alfred workflow to query for EC2 instances and get its ip. Type `ec2ls` on
Alfred to get a list of instances. Type some query text to filter the instances
by tag name.

To access AWS, it will use the credentials stored under `~/.aws/config`. You
can use the command `awsprofile` on Alfred to select which account to use. Also
`awsregion` to select the region.

When you select an instance, it will start an `iTerm2` session and execute a
ssh command using the user `ec2-user` and will try to load a ssh key with the
same name as the session

## Setup

This script makes use of
[deanishe/alfred-workflow](https://github.com/deanishe/alfred-workflow) and
[boto/boto](https://github.com/boto/boto).

To setup, go to the workflow directory and execute the script `setup.sh`.
