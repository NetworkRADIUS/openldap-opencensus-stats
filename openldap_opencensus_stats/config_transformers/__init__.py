
# The transformations process in the order listed here.
from openldap_opencensus_stats.config_transformers.base \
    import ConfigurationTransformationChainSingleton
from openldap_opencensus_stats.config_transformers.snake_case \
    import SnakeCaseConfigurationTransformer                                   # noqa: F401
from openldap_opencensus_stats.config_transformers.metric_dn \
    import MetricDnConfigurationTransformer                                    # noqa: F401
from openldap_opencensus_stats.config_transformers.copy_for_each_database \
    import CopyForEachDatabaseConfigurationTransformer                         # noqa: F401
from openldap_opencensus_stats.config_transformers.child_object \
    import ChildObjectConfigurationTransformer                                 # noqa: F401
from openldap_opencensus_stats.config_transformers.metric_name_interpolation \
    import MetricNameInterpolationConfigurationTransformer                     # noqa: F401
from openldap_opencensus_stats.config_transformers.metric_name \
    import MetricNameConfigurationTransformer                                  # noqa: F401
from openldap_opencensus_stats.config_transformers.metric_query_dn \
    import MetricQueryDnConfigurationTransformer                               # noqa: F401

ConfigurationTransformationChainSingleton().register(MetricDnConfigurationTransformer)
