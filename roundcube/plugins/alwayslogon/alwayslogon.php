<?php

/**
 * This performs automatic login
 *
 * @license GNU GPLv3+
 */
class alwayslogon extends rcube_plugin
{
    private $redirect_query;

    /**
     * Plugin initialization
     */
    #[Override]
    public function init()
    {
        $this->add_hook('startup', [$this, 'startup']);
        $this->add_hook('authenticate', [$this, 'authenticate']);
        $this->add_hook('login_after', array($this, 'login_redirect'));

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
            $this->redirect_query = $_SERVER['QUERY_STRING'];
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
        // The hook carries no port of its own, so the target is passed as
        // host[:port]. Without the port Roundcube connects on 143, which the
        // Dovecot service does not serve.
        $port = getenv('ROUNDCUBEMAIL_DEFAULT_PORT');
        $args['host'] = getenv('ROUNDCUBEMAIL_DEFAULT_HOST') . ($port ? ':' . $port : '');
        $args['cookiecheck'] = false;
        $args['valid'] = true;

        return $args;
    }

    function login_redirect($args)
    {
        // Redirect to the previous QUERY_STRING
        if ($this->redirect_query) {
            header('Location: ./?' . $this->redirect_query);
            exit;
        }

        return $args;
    }
}
