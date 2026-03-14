<source>
  @type tail
  path /var/log/pods/**/*.log
  pos_file /fluentd/log/pods.pos
  tag pod.logs.*
  <parse>
    @type json
    time_key time
    time_format %Y-%m-%dT%H:%M:%S.%LZ
    keep_time_key true
  </parse>
</source>

# Add filter to extract pod and namespace name from tag
<filter pod.logs.**>
  @type record_transformer
  enable_ruby true
  <record>
    namespace ${tag_parts[5].split('_')[0]}
    pod ${tag_parts[5].split('_')[1]}
  </record>
  remove_keys pod_info
</filter>

<match pod.logs.**>
  @type elasticsearch_data_stream
  host {{ .Values.fluentd.config.elasticsearch.host | default (printf "%s-elasticsearch" (include "app.fullname" .)) | quote }}
  port {{ .Values.fluentd.config.elasticsearch.port | default .Values.elasticsearch.service.port | quote }}

  logstash_format true
  include_tag_key true
  data_stream_name {{ .Values.fluentd.config.dataStream.name | quote }}
  data_stream_template_name {{ .Values.fluentd.config.dataStream.templateName | quote }}
  data_stream_ilm_name {{ .Values.fluentd.config.dataStream.ilmName | quote }}
  data_stream_ilm_policy_overwrite true
  data_stream_ilm_policy {
    "policy": {
      "phases": {
        "hot": {
          "min_age": "0ms",
          "actions": {
            "rollover": {
              "max_primary_shard_size": {{ .Values.fluentd.config.dataStream.hotMaxShardSize | quote }},
              "max_age": {{ .Values.fluentd.config.dataStream.hotMaxAge | quote }}
            },
            "set_priority": {
              "priority": 100
            }
          }
        },
        "warm": {
          "min_age": {{ .Values.fluentd.config.dataStream.warmMinAge | quote }},
          "actions": {
            "set_priority": {
              "priority": 50
            }
          }
        },
        "delete": {
          "min_age": {{ .Values.fluentd.config.dataStream.deleteMinAge | quote }},
          "actions": {
            "delete": {
              "delete_searchable_snapshot": true
            }
          }
        }
      }
    }
  }
  fail_on_detecting_es_version_retry_exceed true
  fail_on_putting_template_retry_exceed true
  reconnect_on_error true
  reload_connections false
  reload_on_failure true
  <buffer>
    flush_thread_count {{ .Values.fluentd.config.buffer.flushThreadCount }}
    flush_interval {{ .Values.fluentd.config.buffer.flushInterval | quote }}
    chunk_limit_size {{ .Values.fluentd.config.buffer.chunkLimitSize | quote }}
    queue_limit_length {{ .Values.fluentd.config.buffer.queueLimitLength }}
    retry_max_interval {{ .Values.fluentd.config.buffer.retryMaxInterval }}
    retry_forever true
  </buffer>
</match>
