pragma solidity ^0.8.2;

contract Order {
    address public customer;
    address payable public owner;
    address payable public courier;
    uint public totalAmount;

    enum State { Created, Paid, Pending, Complete }
    State public state;

    modifier onlyCustomer() {
        require(msg.sender == customer, "Invalid customer account.");
        _;
    }

    modifier sufficientFunds() {
        require(customer.balance >= totalAmount, "Insufficient funds.");
        _;
    }

    modifier notPaid() {
        require(state == State.Created, "Transfer already complete.");
        _;
    }

    modifier paid() {
        require(state == State.Paid, "Transfer not complete.");
        _;
    }

    modifier pickedUp() {
        require(state == State.Pending, "Delivery not complete.");
        _;
    }

    constructor(address _customer, uint _totalAmount) {
        owner = payable(msg.sender);
        customer = _customer;
        totalAmount = _totalAmount;
        state = State.Created;
    }

    function pay() external payable onlyCustomer sufficientFunds notPaid {
        state = State.Paid;
    }

    function pickup(address payable _courier) external paid {
        courier = _courier;
        state = State.Pending;
    }

    function delivered() external onlyCustomer pickedUp {
        state = State.Complete;

        uint ownerAmount = (address(this).balance * 80) / 100;
        uint courierAmount = (address(this).balance * 20) / 100;
        owner.transfer(ownerAmount);
        courier.transfer(courierAmount);

    }

}


