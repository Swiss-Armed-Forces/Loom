# Tailscale Setup Instructions

Follow the steps below to set up Tailscale and connect to GitLab runners.

## Instructions

1. **Receive Invite**
   - Ask a project owner for an invite.
   - Log in using a separate identity provider (e.g., GitHub).

2. **Install Tailscale**
   - Download and install Tailscale: [Tailscale Download](https://tailscale.com/download).

3. **Start Tailscale**
   - Run the following command to start Tailscale:

     ```bash
     sudo tailscale up
     ```

4. **Verify Network State**
   - Check the state of your network by running:

     ```bash
     tailscale status
     ```

   - You should see some previous GitLab runners listed.

## Additional Resources

- [Tailscale Documentation](https://tailscale.com/kb/)
- [GitLab Runners](https://docs.gitlab.com/runner/)
