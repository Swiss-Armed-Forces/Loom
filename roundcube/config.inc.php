<?php
/**
 * Adapt defaults from:
 * https://github.com/roundcube/roundcubemail/blob/master/config/defaults.inc.php
 */


// Because why not..
$config['product_name'] = 'Loom Webmail';

// Disable ui elements we don't need
$config['disabled_actions'] = array('compose', 'addressbook', 'reply', 'reply-all', 'forward', 'logout');

// Force use subscription
$config['dont_override'] = ['use_subscriptions'];
$config['use_subscriptions'] = false; // or true

// Default search scope. Supported values:
// 'base' - for current folder (default),
// 'sub' - for current folder and subfolders,
// 'all' - for all folders
$config['search_scope'] = null;

// Default interval for auto-refresh requests (in seconds)
// These are requests for system state updates e.g. checking for new messages, etc.
// Setting it to 0 disables the feature.
$config['refresh_interval'] = 10;

// If true all folders will be checked for recent messages
$config['check_all_folders'] = true;

// Interface layout. Default: 'widescreen'.
//  'widescreen' - three columns
//  'desktop'    - two columns, preview on bottom
//  'list'       - two columns, no preview
// Note: This is ignored for elastic skin
// as the elastic skin is responsive by default
$config['layout'] = 'desktop';

// store draft message is this mailbox
// leave blank if draft messages should not be stored
// NOTE: Use folder names with namespace prefix (INBOX. on Courier-IMAP)
$config['drafts_mbox'] = '';

// store spam messages in this mailbox
// NOTE: Use folder names with namespace prefix (INBOX. on Courier-IMAP)
$config['junk_mbox'] = '';

// store sent message is this mailbox
// leave blank if sent messages should not be stored
// NOTE: Use folder names with namespace prefix (INBOX. on Courier-IMAP)
$config['sent_mbox'] = '';

// move messages to this folder when deleting them
// leave blank if they should be deleted directly
// NOTE: Use folder names with namespace prefix (INBOX. on Courier-IMAP)
$config['trash_mbox'] = '';

// automatically create the above listed default folders on user login
$config['create_default_folders'] = false;

// protect the default folders from renames, deletes, and subscription changes
$config['protect_default_folders'] = false;

// Behavior if a received message requests a message delivery notification (read receipt)
// 0 = ask the user,
// 1 = send automatically,
// 2 = ignore (never send or ask)
// 3 = send automatically if sender is in my contacts, otherwise ask the user
// 4 = send automatically if sender is in my contacts, otherwise ignore
// 5 = send automatically if sender is a trusted sender, otherwise ask the user
// 6 = send automatically if sender is a trusted sender, otherwise ignore
$config['mdn_requests'] = 2;

// Enables display of email address with name instead of a name (and address in title)
$config['message_show_email'] = true;

// X-Frame-Options HTTP header value sent to prevent from Clickjacking.
// Possible values: sameorigin|deny|allow-from <uri>.
// Set to false in order to disable sending the header.
$config['x_frame_options'] = false;
?>