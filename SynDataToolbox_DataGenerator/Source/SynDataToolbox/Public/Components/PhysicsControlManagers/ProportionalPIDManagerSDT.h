#pragma once

#include "CoreMinimal.h"
#include "../PhysicsControlManagers/PIDManagerSDT.h"
#include "ProportionalPIDManagerSDT.generated.h"

UCLASS()
class SYNDATATOOLBOX_API UProportionalPIDManagerSDT : public UObject, public IPIDManagerSDT
{

	GENERATED_BODY()

public:
    /** Add interface function declarations here */
    UProportionalPIDManagerSDT();

    virtual const FString GetPIDManagerName() const override;
    virtual void SetError(TArray<float> Values) override; //differences between set-points and current Values
    virtual bool SetParameters(TArray<float> Parameters) override;
    virtual TArray<float> GetCorrection() override;
    virtual void SetNumControlledVariables(int Num) override; //Define TArray lengths

    UPROPERTY()
        int ControlledVariables = 1.0f;
    UPROPERTY()
        TArray<float> E;
    UPROPERTY()
        TArray<float> U;
    UPROPERTY()
        TArray<float> KP;
};