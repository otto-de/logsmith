# Features

The following document lists descriptions of features and changes that have been introduced to the application.

### Script Toggle

***since 8.3.0***

Running the Profile Group Script can now be enabled or disabled globally.
This is useful in situations where external factors may cause the script to fail (e.g., during disaster recovery), and
you want to avoid modifying the entire configuration each time, or when the script covers a specific use-case that is
not relevant for each login.

See: https://github.com/otto-de/logsmith/tree/main?tab=readme-ov-file#script

### Script Timeout

***since 8.2.0***

The timeout for scripts that are run with login has been proven as way to short and has been increased to 60 seconds.

### Script Paths

***since 8.2.0***

Script paths can now expand the following variables `"${HOME}"`, `"$HOME"`, `${HOME}`, `$HOME` or `~`.

See: https://github.com/otto-de/logsmith/tree/main?tab=readme-ov-file#script

### Application Logs Dialog

***since 8.2.0***

The dialog for the logs has been overhauled. It now updates and trails the log file, so you can see the log in
real-time.

### Help Texts

***since 8.1.0***

Most of the dialogs now have text at the beginning, describing its function and what to expect.

### AWS Config

***since 8.1.0***

In addition to the .aws/credentials, Logsmith also writes the .aws/config to set the region where your operations take
place.
In the past, Logsmith removed any entries it did not know. Now it is limited to configs that affect profiles.

So if you have any global configs like for s3, it will no longer be deleted.

### Getting Started Guide

***since 8.1.0***

For all the logsmith-starter out there, the README now includes a much-needed Getting Started section, explaining how to
use and set up the application (feedback is greatly appreciated).

### Service Profile

***since 8.0.0***

In the past, we sometimes struggled with IAM policies. When we're developing a service, we usually run it with our own
developer privileges locally, so that problems with insufficient access rights usually become apparent after deployment.
To encounter these problems early, one would have to manually assume the intended service role locally, which can be a
bit of a hassle.

If you ever encountered this problem, Logsmith is going to make your life easier.
After logging in and selecting a profile group, you can now fetch every role that is assumable from the given source
profile.
From there, you can filter and select a role that you would like to assume, which is then saved in a "service" profile.

Every role selected this way will always be written in the "service" profile. This way, the startup for applications
with their intended roles can be standardized. Like setting "AWS_PROFILE=service" before startup.

The selected role is saved, meaning that it will always be assumed when selecting the same profile group.
To reset this (remove the service role), you can use the "reset" button in the dialog.

If you want to quickly jump between roles, there is also a history which lets you select one of your previous
profile-role combinations.

See: https://github.com/otto-de/logsmith/tree/main?tab=readme-ov-file#service-profile

### Script run after login

***since 8.0.0***

If you have some additional stuff you need to do after login, like login into EKS or ECS or the like, logsmith can do
that for you.
Each profile group now has a script option, which lets you specify and run a script (you can even add arguments, if you
like).

See: https://github.com/otto-de/logsmith/tree/main?tab=readme-ov-file#script

### Account Id to Clipboard

***since 8.0.0***

If I were to sum it up, I guess I have spent a substantial amount of time opening the logsmith config to copy one of the
account ids.
This is now easier than ever! After login you get two new sub menus, allowing you to copy a profile name or account id
of the current profile group with one click.

### Background Tasks

***since 8.0.0***

All operations are now done in the background, and do not block the UI anymore.
There is also a "busy" icon now, telling you that an operation is underway.

