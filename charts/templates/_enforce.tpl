
{{/*
This template enforces that two specific values in the values.yaml file are equal.
If they are not, Helm will fail with an error during rendering.
This is useful for ensuring consistency between values that must always match,
even when users override them via --set or a custom values file.
*/}}
