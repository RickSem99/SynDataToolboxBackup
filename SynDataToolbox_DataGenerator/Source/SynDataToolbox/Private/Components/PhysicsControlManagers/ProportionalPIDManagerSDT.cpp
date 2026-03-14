#include "Components/PhysicsControlManagers/ProportionalPIDManagerSDT.h"

UProportionalPIDManagerSDT::UProportionalPIDManagerSDT()
{
    E = TArray<float>();
    U = TArray<float>();
    KP = TArray<float>();
}

const FString UProportionalPIDManagerSDT::GetPIDManagerName() const
{
    return FString("Proportional Regolator");
}

void UProportionalPIDManagerSDT::SetError(TArray<float> Values)
{
    if (Values.Num() == 1 * ControlledVariables) {  
        for (int i = 0; i < ControlledVariables; i += 2)
        {
            E[i] = Values[i];
            U[i] = KP[i] * E[i];
            E[i + 1] = Values[i + 1];
            U[i + 1] = KP[i + 1] * E[i + 1];
        }
    }
}

bool UProportionalPIDManagerSDT::SetParameters(TArray<float> Parameters)
{
    
    if (Parameters.Num() == 1*ControlledVariables) {
        for (int i = 0; i < ControlledVariables; i+=2) 
        {
            KP[i] = Parameters[i];
            KP[i + 1] = Parameters[i+1];
        }
        return true;
    }
    return false;
}

TArray<float> UProportionalPIDManagerSDT::GetCorrection()
{
    return U;
}

void UProportionalPIDManagerSDT::SetNumControlledVariables(int Num)
{
    ControlledVariables = Num;
    E.Empty();
    E.SetNum(ControlledVariables);
    U.Empty();
    U.SetNum(ControlledVariables);
    KP.Empty();
    KP.SetNum(ControlledVariables);
}
