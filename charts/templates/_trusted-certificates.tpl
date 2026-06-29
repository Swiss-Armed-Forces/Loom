{{/*
Init container that installs trusted CA certificates into a shared emptyDir volume.
Only rendered when .Values.trustedCertificates.certs is non-empty.
Usage: {{- with include "app.trustedCerts.initContainer" . }}{{ . | nindent 8 }}{{- end }}
*/}}
{{- define "app.trustedCerts.initContainer" -}}
{{- if .Values.trustedCertificates.certs }}
- name: ca-installer
  image: {{ .Values.image.registry }}/{{ .Values.trustedCertificates.initContainer.image.repository }}:{{ default (default .Chart.AppVersion .Values.image.tag) .Values.trustedCertificates.initContainer.image.tag }}
  imagePullPolicy: {{ .Values.image.pullPolicy }}
  command:
    - sh
    - -c
    - |
      set -eu
      cp /ca-certificates-configmap/*.crt /usr/local/share/ca-certificates/
      update-ca-certificates
      cp -r /etc/ssl/. /ca-bundle/
  volumeMounts:
    - name: ca-certificates-configmap
      mountPath: /ca-certificates-configmap
      readOnly: true
    - name: ca-bundle
      mountPath: /ca-bundle
  {{- if .Values.trustedCertificates.initContainer.resources }}
  resources: {{- toYaml .Values.trustedCertificates.initContainer.resources | nindent 4 }}
  {{- end }}
{{- end }}
{{- end -}}

{{/*
Volumes for the trusted CA certificates init container pattern.
Only rendered when .Values.trustedCertificates.certs is non-empty.
Usage: {{- with include "app.trustedCerts.volumes" . }}{{ . | nindent 8 }}{{- end }}
*/}}
{{- define "app.trustedCerts.volumes" -}}
{{- if .Values.trustedCertificates.certs }}
- name: ca-certificates-configmap
  configMap:
    name: {{ include "app.fullname" . }}-trusted-certificates
- name: ca-bundle
  emptyDir: {}
{{- end }}
{{- end -}}

{{/*
VolumeMount for the trusted CA bundle in main containers.
Only rendered when .Values.trustedCertificates.certs is non-empty.
Usage: {{- with include "app.trustedCerts.volumeMount" . }}{{ . | nindent 12 }}{{- end }}
*/}}
{{- define "app.trustedCerts.volumeMount" -}}
{{- if .Values.trustedCertificates.certs }}
- name: ca-bundle
  mountPath: /etc/ssl
{{- end }}
{{- end -}}
