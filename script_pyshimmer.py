from pyshimmer.dev.channels import EChannelType
canali_ecg = [c for c in EChannelType if 'ECG' in c.name or 'EXG' in c.name]
for c in canali_ecg:
    print(c.name, c.value)