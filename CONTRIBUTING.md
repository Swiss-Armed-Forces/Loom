# Contributing Guidelines for Loom

Welcome to the Loom project! Contributions are the foundation of our success, and we’re excited to have you involved.
These guidelines will help ensure smooth collaboration and effective contributions. Please review them carefully before starting.

## Table of Contents

1. [Guidelines for Design Discussions](#guidelines-for-design-discussions)
2. [Development Workflow and Merge Requests](#development-workflow-and-merge-requests)
3. [Acknowledgments](#acknowledgments)

## Guidelines for Design Discussions

To maintain transparency and traceability:

- **Do not hold important design discussions in Rocket.Chat.**
  Always use **issues** or **merge request comments** to discuss design and technical decisions.This ensures all discussions
  are visible, well-documented, and accessible to the entire team.

## Development Workflow and Merge Requests

1. **Start with an Issue**
   - Always create an issue first to describe the problem, feature, or enhancement you wish to address.
   This ensures alignmentand facilitates discussion before implementation.
   - Use GitLab’s **"Create Merge Request"** button directly from the issue.
   This automatically links the issue to the merge request and generates a branch with a default name.

2. **Branch Naming**
   - If a branch is generated from an issue using the **"Create Merge Request"** button, use the default branch name.
   - If you manually create a branch, use descriptive names prefixed with `feature/` or `bugfix/`, e.g., `feature/add-user-authentication`.

3. **Open Merge Requests Early**
   - Open your merge request (MR) as early as possible, even if no code has been written yet.
   An empty MR serves as a platform for early discussions and feedback.

4. **Draft Merge Requests**
   - All new MRs should initially be marked as **Draft**.
   This indicates that the MR is a work in progress and not yet ready for merging.
   - The **Draft** status should only be removed when the assignee deems the MR ready for merging.
   - While in Draft status, MRs do not require reviews and can generally be ignored by reviewers
   unless the assignee specifically requests a review.

5. **Use Meaningful Titles and Descriptions**
   - Use a clear and meaningful title for your MR. This title will be used to generate release notes,
   so ensure it accurately reflects the purpose of the MR.
   - Keep the MR description up-to-date with the scope and context of your work.
   Use it to explain implementation details or specific considerations.

6. **Linking Issues to Merge Requests**
   - Link your MR to any related issue by including the following in the MR description:

     ```plaintext
     Closes #issue-number
     ```

   - This automatically closes the issue when the MR is merged, keeping the issue tracker organized.

7. **Labels for Issues and MRs**
   - Add appropriate labels to your issues and MRs. This helps organize and categorize them,
   making it easier for collaborators to understand their purpose.

8. **Commit Messages and Squash Merging**
   - Since we use squash merging, individual commit messages are not critical.
   Instead, focus on updating the MR title and description, as these will be used for release notes.
   - Squash merging combines all commits into a single commit during merge, simplifying the history.

9. **Roles in Merge Requests**
   - **Assignee**: The person actively working on the MR.
   They are responsible for making changes, addressing feedback, and ensuring the MR meets project standards.
   - **Reviewer**: The person responsible for reviewing the MR, providing feedback, and merging it once it is approved.
   Reviewers generally ignore **Draft** MRs unless explicitly requested by the assignee.

10. **Code Review Guidelines**
    - Reviewers ensure the code adheres to project standards, is thoroughly tested, and does not introduce regressions.
    - They also verify that the MR title and description are clear and complete for release notes.

## Acknowledgments

Thank you for contributing to Loom! Your contributions are invaluable to the project’s success.
If you have any questions or need guidance, don’t hesitate to reach out through the project’s issue tracker
or merge request comments.

Let’s build something amazing together. Happy coding! 🚀
