# Generated manually to capture initial CRM models
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


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
                ('phone', models.CharField(max_length=15, unique=True)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('card_number', models.CharField(max_length=50, unique=True)),
                ('start_date', models.DateField(default=django.utils.timezone.localdate)),
                ('end_date', models.DateField()),
                ('status', models.CharField(choices=[('active', 'Active'), ('expired', 'Expired'), ('blocked', 'Blocked')], default='active', max_length=20)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='crm.customer')),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='ProgramSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
                ('membership_fee', models.PositiveIntegerField(default=25000)),
                ('membership_duration_months', models.PositiveIntegerField(default=3)),
                ('discount_percent', models.PositiveIntegerField(default=10)),
                ('min_amount_for_stamp', models.PositiveIntegerField(default=50000)),
                ('reward_stamp_1_type', models.CharField(choices=[('none', 'No Reward'), ('free_drink', 'Free Drink'), ('voucher_50k', 'Voucher 50k')], default='free_drink', max_length=20)),
                ('reward_stamp_10_type', models.CharField(choices=[('none', 'No Reward'), ('free_drink', 'Free Drink'), ('voucher_50k', 'Voucher 50k')], default='voucher_50k', max_length=20)),
            ],
            options={'abstract': False},
        ),
        migrations.CreateModel(
            name='StampCycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('cycle_number', models.PositiveIntegerField()),
                ('is_closed', models.BooleanField(default=False)),
                ('membership', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cycles', to='crm.membership')),
            ],
            options={'unique_together': {('membership', 'cycle_number')}},
        ),
        migrations.CreateModel(
            name='Stamp',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('number', models.PositiveIntegerField()),
                ('reward_type', models.CharField(choices=[('none', 'No Reward'), ('free_drink', 'Free Drink'), ('voucher_50k', 'Voucher 50k')], default='none', max_length=20)),
                ('redeemed_at', models.DateTimeField(blank=True, null=True)),
                ('pos_receipt_number', models.CharField(blank=True, max_length=100, null=True)),
                ('transaction_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('cycle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='stamps', to='crm.stampcycle')),
            ],
            options={'unique_together': {('cycle', 'number')}},
        ),
    ]
