{{/*
_helpers.tpl — Reusable template snippets shared across all chart templates.

Usage:
  {{ include "predscale.labels" . }}
  {{ include "predscale.selectorLabels" . }}
*/}}

{{/*
Common labels applied to every resource in the chart.
Helm best-practice: always include app.kubernetes.io/* labels for tooling compatibility.
*/}}
{{- define "predscale.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Selector labels used in Deployment.spec.selector and Service.spec.selector.
Must NOT include mutable fields like chart version (changing them breaks rolling updates).
*/}}
{{- define "predscale.selectorLabels" -}}
app.kubernetes.io/name: {{ .name }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
