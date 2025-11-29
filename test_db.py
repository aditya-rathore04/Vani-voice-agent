from app.database import get_doctor_info

print(get_doctor_info("sharma"))   # Should find Dr. Sharma
print(get_doctor_info("dr gpta"))  # Should find Dr. Gupta (typo)
print(get_doctor_info("pizza"))    # Should be None