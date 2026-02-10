# Generated migration for ScenarioImage and SceneDescriptionResponse models

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('therapy', '0002_therapysession_created_by_and_more'),  # Depend on latest migration
    ]

    operations = [
        migrations.CreateModel(
            name='ScenarioImage',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('image', models.ImageField(upload_to='scenarios/')),
                ('expected_description', models.TextField(help_text='Expected key elements child should describe')),
                ('level', models.IntegerField(
                    choices=[(1, 'Easy'), (2, 'Medium'), (3, 'Hard')],
                    default=1
                )),
                ('key_elements', models.JSONField(blank=True, default=list, help_text='List of key things to describe')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'indexes': [
                    models.Index(fields=['level'], name='therapy_scen_level_idx'),
                    models.Index(fields=['is_active'], name='therapy_scen_active_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='SceneDescriptionResponse',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('child_response', models.TextField(help_text="Child's description of the scenario")),
                ('llm_feedback', models.TextField(blank=True, default='', help_text='Detailed feedback from LLM')),
                ('llm_score', models.IntegerField(blank=True, help_text='0-100 score from LLM', null=True)),
                ('key_elements_found', models.JSONField(blank=True, default=list, help_text='Which key elements were mentioned')),
                ('clarity_score', models.IntegerField(blank=True, help_text='0-10 clarity/coherence', null=True)),
                ('completeness_score', models.IntegerField(blank=True, help_text='0-10 how complete the description is', null=True)),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('scenario', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='responses', to='therapy.scenarioimage')),
                ('trial', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scene_responses', to='therapy.sessiontrial')),
            ],
            options={
                'indexes': [
                    models.Index(fields=['trial'], name='therapy_scen_trial_idx'),
                    models.Index(fields=['scenario'], name='therapy_scen_scenario_idx'),
                ],
            },
        ),
    ]
