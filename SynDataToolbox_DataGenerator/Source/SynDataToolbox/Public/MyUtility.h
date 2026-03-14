// MyUtility.h
#pragma once

#include "CoreMinimal.h"
#include "Kismet/BlueprintFunctionLibrary.h"
#include "MyUtility.generated.h"

UCLASS()
class UMyUtility : public UBlueprintFunctionLibrary
{
    GENERATED_BODY()

public:
    UFUNCTION(BlueprintCallable, Category = "Debug")
    static void DrawSinusoidalCircle(UObject* WorldContextObject, FVector Center, float Radius, float Hieght, int32 NumberOfPoints);
};
