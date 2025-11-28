# Generated manually because Django isn't available in the execution environment.
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=50)),
                ('phone', models.CharField(blank=True, max_length=15, null=True)),
                ('email', models.EmailField(max_length=254, unique=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('card_number', models.CharField(max_length=50, unique=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('status', models.CharField(choices=[('active', 'Active'), ('expired', 'Expired'), ('blocked', 'Blocked')], default='active', max_length=20)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='crm.customer')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ProgramSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('min_transaction_amount', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('stamps_per_reward', models.PositiveIntegerField(default=10)),
                ('reward_label', models.CharField(default='Reward', max_length=100)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='StampCycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cycle_number', models.PositiveIntegerField()),
                ('is_active', models.BooleanField(default=True)),
                ('closed_at', models.DateTimeField(blank=True, null=True)),
                ('membership', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cycles', to='crm.membership')),
            ],
            options={
                'ordering': ['membership', 'cycle_number'],
            },
        ),
        migrations.CreateModel(
            name='Stamp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_reward', models.BooleanField(default=False)),
                ('note', models.CharField(blank=True, max_length=255)),
                ('cycle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stamps', to='crm.stampcycle')),
                ('membership', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stamps', to='crm.membership')),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.AlterUniqueTogether(
            name='stampcycle',
            unique_together={('membership', 'cycle_number')},
        ),
    ]
