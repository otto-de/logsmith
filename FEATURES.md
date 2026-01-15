# Features

The following document lists descriptions of features and changes that have been introduced to the application.


### Profile verification

***since 9.1.0-rc.3***

After login, Logsmith verifies profiles every 5 minutes to ensure they remain valid and usable. The tray icon context
menu shows an indicator for each profile (checkmark or X), and a new application state/tray icon appears if one or more
profiles are invalid. 
This is especially useful when `sso_interval` is set to 0 (disabled), since it highlights when your SSO session has expired and you need to log in again.


### Write Mode

***since 9.1.0-rc.2***

SSO credentials can now be written as "credentials" by setting the config option `write_mode` to `keys`.
This helps when a tool expects static access keys but you still want to use SSO login.

Both `auth_modes` (`sso` and `key`) default to their respective mode, which is `sso` or `key`. But please note that aside from the default, the only real open is `auth_mode = sso` with `write_mode = key`.

`auth_mode = key` with `write_mode = sso` is not available because SSO sessions cannot be synthesized from a access-key based authentication.

### SSO Login Interval

***since 9.1.0-rc.1***

The validity of SSO sessions can be configured, so there is now the config option `sso_interval` to configurate how in which interval Logsmith should refresh the login.

This can be set as a default or for every profile group.

Also, because the SSO login will always open a browser windows, which takes away the focus and can be quite bothersome, the refresh can be disabled entirely by setting the interval to 0.

### Auth Mode (AWS SSO Login)

***since 9.0.0***

Each profile group can now configure an `auth_mode` to control how login is performed. The options are `sso` and `key`.
Use `sso` to authenticate via AWS SSO sessions, or `key` to use access-key based login for that profile group.

To use the new `sso` mode, you must add at least one SSO session, which works similar to `access-keys`. Also `sso-session` must start with `sso`.
This is so that logsmith does not remove them when doing a cleanup.

As of now, Logsmith uses the `aws cli` to do the SSO Login, because boto3 does not support the login (yet).

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
