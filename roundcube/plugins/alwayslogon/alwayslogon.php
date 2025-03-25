<?php

/**
 * This performs automatic login
 *
 * @license GNU GPLv3+
 */
class alwayslogon extends rcube_plugin
{
    public $task = 'login';

    /**
     * Plugin initialization
     */
    #[Override]
    public function init()
    {
        $this->add_hook('startup', [$this, 'startup']);
        $this->add_hook('authenticate', [$this, 'authenticate']);
    }

    /**
     * 'startup' hook handler
     *
     * @param array $args Hook arguments
     *
     * @return array Hook arguments
     */
    public function startup($args)
    {
        // change action to login
        if (empty($_SESSION['user_id'])) {
            $args['action'] = 'login';
        }

        return $args;
    }

    /**
     * 'authenticate' hook handler
     *
     * @param array $args Hook arguments
     *
     * @return array Hook arguments
     */
    public function authenticate($args)
    {
        $args['user'] = 'user';
        $args['pass'] = 'pass';
        $args['host'] = $_SERVER['REMOTE_ADDR'];
        $args['cookiecheck'] = false;
        $args['valid'] = true;

        return $args;
    }
}
