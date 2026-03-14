#pragma once
#include "PIDManagerSDT.generated.h"

UINTERFACE(MinimalAPI, Blueprintable)
class UPIDManagerSDT : public UInterface
{
    GENERATED_BODY()
};

class SYNDATATOOLBOX_API IPIDManagerSDT
{
    GENERATED_BODY()

public:
    /** Add interface function declarations here */
    virtual const FString GetPIDManagerName() const; 
    virtual void SetError(TArray<float> Values); //differences between set-points and current Values
    virtual bool SetParameters(TArray<float> Params);
    virtual TArray<float> GetCorrection();
    virtual void SetNumControlledVariables(int Num);
};