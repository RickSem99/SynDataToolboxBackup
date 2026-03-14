#include "Components/PhysicsControlManagers/PIDManagerSDT.h"

const FString IPIDManagerSDT::GetPIDManagerName() const
{
    return FString("NO PID IMPLEMENTATION");
}

void IPIDManagerSDT::SetError(TArray<float> Values)
{
}

bool IPIDManagerSDT::SetParameters(TArray<float> Params)
{
    return false;
}

TArray<float> IPIDManagerSDT::GetCorrection()
{
    return TArray<float>();
}

void IPIDManagerSDT::SetNumControlledVariables(int Num)
{
}
