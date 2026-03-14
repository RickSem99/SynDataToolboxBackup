#include "Components/PhysicsControlManagers/UniformPhysicsManagerSDT.h"

UUniformPhysicsManagerSDT::UUniformPhysicsManagerSDT()
{
}

const FString UUniformPhysicsManagerSDT::GetPhysicsManagerName() const
{
	return FString("UNIFORM PHYSICS MANAGER");
}

TArray<float> UUniformPhysicsManagerSDT::GetCurrentOutputs()
{
	return TArray<float>({ (1 - FrictionParameter) * Current_Linear_Velocity,Current_Linear_Acceleration,(1 - AngularFrictionParameter) * Current_Angular_Velocity, (Current_Angular_Acceleration * PI) / 180 });

}

void UUniformPhysicsManagerSDT::GetActorReference(AActor* Agent, FHitResult* ActorHit)
{
	AgentToManage = Agent;
	HitHandler = ActorHit;

	//SET ROTATION AND LOCATION
	CurrentPosition = AgentToManage->GetActorLocation();
	OldPosition = CurrentPosition;

	CurrentRotation = AgentToManage->GetActorRotation();
	CurrentRotation.Normalize();
	OldRotation = CurrentRotation;
}

bool UUniformPhysicsManagerSDT::Reset()
{
	//Restore Original Values
	Current_Angular_Velocity = 0.0;
	Current_Linear_Velocity = 0.0f;

	CurrentPosition = AgentToManage->GetActorLocation();
	OldPosition = CurrentPosition;
	CurrentRotation = AgentToManage->GetActorRotation();
	OldRotation = CurrentRotation;
	return true;
}

void UUniformPhysicsManagerSDT::SetPhysicsSettings(TArray<float> Settings)
{
	// current order: 
	// AgentMass,	AgentLength, AgentWidth, 
	// FrictionParameter, AngularFrictionParameter
	// MAX_FORCE, MAX_MOMENTUM, MIN_FORCE, MIN_MOMENTUM

	if (Settings.Num() == 9)
	{
		AgentMass = Settings[0];
		AgentLength = Settings[1];
		AgentWidth = Settings[2];
		FrictionParameter = Settings[3];
		AngularFrictionParameter = Settings[4];
		MAX_FORCE = Settings[5];
		MAX_MOMENTUM = Settings[6];
		MIN_FORCE = Settings[7];
		MIN_MOMENTUM = Settings[8];
	}
}

TArray<float> UUniformPhysicsManagerSDT::Compute(TArray<float> RegulationVector)
{
	//compute linear Velocity
	FVector CurrentLinearVelocity = (1 - FrictionParameter) * (AgentToManage->GetActorLocation() - OldPosition);
	FVector AgentForwardVector = AgentToManage->GetActorForwardVector(); //Already normalized

	/* | is dot symbol for dot product between two vectors*/
	float CurrentVelocityForward = CurrentLinearVelocity | (AgentForwardVector); //scalar velocity on forward direction
	float IdealAcceleration = RegulationVector[0];
	float IdealForce = AgentMass * IdealAcceleration;
	float AuxNextAcceleration = fmin(IdealForce / AgentMass, MAX_FORCE / AgentMass);
	Current_Linear_Acceleration = fmax(AuxNextAcceleration, MIN_FORCE / AgentMass);
	FVector NextAccelerationVector = (Current_Linear_Acceleration * AgentForwardVector);

	OldPosition = AgentToManage->GetActorLocation();
	CurrentPosition = OldPosition + (CurrentLinearVelocity + 0.5 * NextAccelerationVector); //update after

	/*Angular Velocity*/
	//Current_Angular_Velocity* FRotator(0.0, 1.0, 0.0)
	FRotator RotatorYaw = FRotator(0.0f, 1.0f, 0.0f);
	FRotator CurrentAngularVelocityRotator = (1 - AngularFrictionParameter) * (CurrentRotation - OldRotation);
	float IdealAngularAcceleration = RegulationVector[1] * 180 / PI; //CAST FROM RADIANS TO DEG
	float Inertia = ((pow(AgentWidth * 0.01, 2) + pow(AgentLength * 0.01, 2)) * AgentMass) / 12;
	float IdealMomentumAngularAcceleration = Inertia * IdealAngularAcceleration;
	float AuxNextAngularAcceleration = fmin(MAX_MOMENTUM / Inertia, IdealMomentumAngularAcceleration / Inertia);
	Current_Angular_Acceleration = fmax(MIN_MOMENTUM / Inertia, AuxNextAngularAcceleration / Inertia);
	FRotator NextAccelerationRotator = Current_Angular_Acceleration * RotatorYaw;

	OldRotation = CurrentRotation;
	CurrentRotation = OldRotation + CurrentAngularVelocityRotator + 0.5 * NextAccelerationRotator;

	//real update of Rotation and Location
	AgentToManage->SetActorLocationAndRotation(CurrentPosition, CurrentRotation, true, HitHandler);
	Current_Linear_Velocity = ((AgentToManage->GetActorLocation() - OldPosition) | AgentForwardVector);
	Current_Angular_Velocity = ((CurrentRotation.Yaw - OldRotation.Yaw)) * PI / 180; //IN RADIANS (RADIANS PER DELTATIME)	

	return TArray<float>({ Current_Linear_Velocity,Current_Linear_Acceleration,Current_Angular_Velocity, Current_Angular_Acceleration * (PI / 180) });
}